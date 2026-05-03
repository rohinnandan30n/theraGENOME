-- PostgreSQL audit log table with automatic trigger for variant results
CREATE TABLE IF NOT EXISTS variant_audit_log (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    result_id UUID NOT NULL REFERENCES variant_results(result_id) ON DELETE CASCADE,
    patient_id UUID NOT NULL,
    operation VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,
    new_data JSONB,
    changed_fields TEXT[],
    changed_by UUID,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_variant_audit_log_result_id ON variant_audit_log(result_id);
CREATE INDEX IF NOT EXISTS idx_variant_audit_log_patient_id ON variant_audit_log(patient_id);
CREATE INDEX IF NOT EXISTS idx_variant_audit_log_changed_at ON variant_audit_log(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_variant_audit_log_operation ON variant_audit_log(operation);
CREATE INDEX IF NOT EXISTS idx_variant_audit_log_patient_result ON variant_audit_log(patient_id, result_id);

-- Trigger function to automatically log changes
CREATE OR REPLACE FUNCTION variant_results_audit_trigger()
RETURNS TRIGGER AS $$
DECLARE
    v_changed_fields TEXT[];
BEGIN
    -- Build the list of changed fields
    IF TG_OP = 'INSERT' THEN
        v_changed_fields := ARRAY[]::TEXT[];
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.prediction <> NEW.prediction THEN v_changed_fields := array_append(v_changed_fields, 'prediction'); END IF;
        IF OLD.confidence <> NEW.confidence THEN v_changed_fields := array_append(v_changed_fields, 'confidence'); END IF;
        IF OLD.clinical_notes <> NEW.clinical_notes THEN v_changed_fields := array_append(v_changed_fields, 'clinical_notes'); END IF;
        IF OLD.metadata <> NEW.metadata THEN v_changed_fields := array_append(v_changed_fields, 'metadata'); END IF;
        IF OLD.updated_at <> NEW.updated_at THEN v_changed_fields := array_append(v_changed_fields, 'updated_at'); END IF;
    END IF;

    -- Insert audit record
    INSERT INTO variant_audit_log (
        result_id, patient_id, operation, old_data, new_data,
        changed_fields, changed_by, changed_at
    ) VALUES (
        CASE WHEN TG_OP = 'DELETE' THEN OLD.result_id ELSE NEW.result_id END,
        CASE WHEN TG_OP = 'DELETE' THEN OLD.patient_id ELSE NEW.patient_id END,
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN row_to_json(NEW) ELSE NULL END,
        v_changed_fields,
        COALESCE(current_setting('audit.user_id', true)::UUID, NULL),
        CURRENT_TIMESTAMP
    );

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if it exists
DROP TRIGGER IF NOT EXISTS variant_results_audit_trigger ON variant_results;

-- Create trigger for automatic audit logging
CREATE TRIGGER variant_results_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON variant_results
FOR EACH ROW EXECUTE FUNCTION variant_results_audit_trigger();
