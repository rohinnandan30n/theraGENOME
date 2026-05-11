// Data access layer for variant results
import { query, queryObject, queryArray, transaction } from "./db.ts";
import {
  VariantResult,
  VariantAuditLog,
  CreateVariantResultRequest,
  UpdateVariantResultRequest,
  ListVariantResultsQuery,
  ListResponse,
  StatisticsResponse,
} from "./types.ts";

// Generate a simple UUID v4
function generateUUID(): string {
  return crypto.randomUUID();
}

/**
 * Create a new variant result
 */
export async function createVariantResult(
  patientId: string,
  data: CreateVariantResultRequest,
  userId: string
): Promise<VariantResult> {
  const resultId = generateUUID();
  const now = new Date().toISOString();

  const result = await query<VariantResult>(
    `
    INSERT INTO variant_results (
      result_id, patient_id, variant_id, chrom, pos, ref, alt,
      prediction, confidence, probabilities, model_version,
      feature_importance, clinical_notes, created_by, created_at,
      updated_at, is_deleted, metadata
    )
    VALUES (
      $1, $2, $3, $4, $5, $6, $7,
      $8, $9, $10, $11,
      $12, $13, $14, $15,
      $16, false, $17
    )
    RETURNING *;
    `,
    [
      resultId,
      patientId,
      data.variant_id,
      data.chrom,
      data.pos,
      data.ref,
      data.alt,
      data.prediction,
      data.confidence,
      JSON.stringify(data.probabilities),
      data.model_version,
      JSON.stringify(data.feature_importance),
      data.clinical_notes,
      userId,
      now,
      now,
      JSON.stringify(data.metadata),
    ]
  );

  return result!;
}

/**
 * Get a single variant result
 */
export async function getVariantResult(
  resultId: string
): Promise<VariantResult | null> {
  const result = await query<VariantResult>(
    "SELECT * FROM variant_results WHERE result_id = $1 AND is_deleted = false;",
    [resultId]
  );
  return result;
}

/**
 * Update a variant result
 */
export async function updateVariantResult(
  resultId: string,
  data: UpdateVariantResultRequest,
  userId: string
): Promise<VariantResult> {
  const now = new Date().toISOString();
  const updates: string[] = [];
  const params: unknown[] = [resultId];
  let paramIndex = 2;

  if (data.prediction) {
    updates.push(`prediction = $${paramIndex}`);
    params.push(data.prediction);
    paramIndex++;
  }

  if (data.clinical_notes !== undefined) {
    updates.push(`clinical_notes = $${paramIndex}`);
    params.push(data.clinical_notes);
    paramIndex++;
  }

  if (data.metadata) {
    updates.push(`metadata = $${paramIndex}`);
    params.push(JSON.stringify(data.metadata));
    paramIndex++;
  }

  updates.push(`updated_at = $${paramIndex}`);
  params.push(now);

  const updateClause = updates.join(", ");
  const sql = `
    UPDATE variant_results
    SET ${updateClause}
    WHERE result_id = $1 AND is_deleted = false
    RETURNING *;
  `;

  const result = await query<VariantResult>(sql, params);
  return result!;
}

/**
 * Soft delete a variant result
 */
export async function softDeleteVariantResult(
  resultId: string,
  userId: string
): Promise<void> {
  const now = new Date().toISOString();

  await queryArray(
    `
    UPDATE variant_results
    SET is_deleted = true, deleted_at = $2
    WHERE result_id = $1 AND is_deleted = false;
    `,
    [resultId, now]
  );
}

/**
 * List patient variant results with filtering
 */
export async function listPatientVariantResults(
  patientId: string,
  queryParams: ListVariantResultsQuery
): Promise<ListResponse<VariantResult>> {
  const limit = Math.min(queryParams.limit || 20, 100);
  const offset = queryParams.offset || 0;
  const sortBy = queryParams.sort_by || "created_at";
  const sortOrder = queryParams.sort_order || "DESC";

  // Build WHERE clause
  const whereConditions: string[] = [
    "patient_id = $1",
    `is_deleted = ${queryParams.include_deleted ? "true OR is_deleted = false" : "false"}`,
  ];
  const params: unknown[] = [patientId];
  let paramIndex = 2;

  if (queryParams.start_date) {
    whereConditions.push(`created_at >= $${paramIndex}`);
    params.push(queryParams.start_date);
    paramIndex++;
  }

  if (queryParams.end_date) {
    whereConditions.push(`created_at <= $${paramIndex}`);
    params.push(queryParams.end_date);
    paramIndex++;
  }

  if (queryParams.prediction) {
    whereConditions.push(`prediction = $${paramIndex}`);
    params.push(queryParams.prediction);
    paramIndex++;
  }

  if (queryParams.model_version) {
    whereConditions.push(`model_version = $${paramIndex}`);
    params.push(queryParams.model_version);
    paramIndex++;
  }

  const whereClause = whereConditions.join(" AND ");

  // Get total count
  const countResult = await query<{ count: number }>(
    `SELECT COUNT(*) as count FROM variant_results WHERE ${whereClause};`,
    params
  );
  const total = countResult?.count || 0;

  // Get paginated results
  const results = await queryObject<VariantResult>(
    `
    SELECT * FROM variant_results
    WHERE ${whereClause}
    ORDER BY ${sortBy} ${sortOrder}
    LIMIT ${limit} OFFSET ${offset};
    `,
    params
  );

  return {
    data: results,
    total,
    limit,
    offset,
    has_next: offset + limit < total,
  };
}

/**
 * Get audit log for a specific variant result
 */
export async function getVariantResultAuditLog(
  resultId: string,
  limit: number = 50,
  offset: number = 0
): Promise<ListResponse<VariantAuditLog>> {
  const actualLimit = Math.min(limit, 100);

  const countResult = await query<{ count: number }>(
    "SELECT COUNT(*) as count FROM variant_audit_log WHERE result_id = $1;",
    [resultId]
  );
  const total = countResult?.count || 0;

  const logs = await queryObject<VariantAuditLog>(
    `
    SELECT * FROM variant_audit_log
    WHERE result_id = $1
    ORDER BY changed_at DESC
    LIMIT $2 OFFSET $3;
    `,
    [resultId, actualLimit, offset]
  );

  return {
    data: logs,
    total,
    limit: actualLimit,
    offset,
    has_next: offset + actualLimit < total,
  };
}

/**
 * Get audit log for a patient
 */
export async function getPatientAuditLog(
  patientId: string,
  limit: number = 50,
  offset: number = 0,
  startDate?: string,
  endDate?: string
): Promise<ListResponse<VariantAuditLog>> {
  const actualLimit = Math.min(limit, 100);
  const whereConditions: string[] = ["patient_id = $1"];
  const params: unknown[] = [patientId];
  let paramIndex = 2;

  if (startDate) {
    whereConditions.push(`changed_at >= $${paramIndex}`);
    params.push(startDate);
    paramIndex++;
  }

  if (endDate) {
    whereConditions.push(`changed_at <= $${paramIndex}`);
    params.push(endDate);
    paramIndex++;
  }

  const whereClause = whereConditions.join(" AND ");

  const countResult = await query<{ count: number }>(
    `SELECT COUNT(*) as count FROM variant_audit_log WHERE ${whereClause};`,
    params
  );
  const total = countResult?.count || 0;

  const logs = await queryObject<VariantAuditLog>(
    `
    SELECT * FROM variant_audit_log
    WHERE ${whereClause}
    ORDER BY changed_at DESC
    LIMIT ${actualLimit} OFFSET ${offset};
    `,
    params
  );

  return {
    data: logs,
    total,
    limit: actualLimit,
    offset,
    has_next: offset + actualLimit < total,
  };
}

/**
 * Get prediction statistics for a patient
 */
export async function getPredictionStatistics(
  patientId: string
): Promise<StatisticsResponse["statistics"]> {
  const result = await query<{
    total: number;
    pathogenic_count: number;
    benign_count: number;
    vus_count: number;
    avg_confidence: number;
    last_result_date: string | null;
  }>(
    `
    SELECT
      COUNT(*) as total,
      SUM(CASE WHEN prediction = 'Pathogenic' THEN 1 ELSE 0 END) as pathogenic_count,
      SUM(CASE WHEN prediction = 'Benign' THEN 1 ELSE 0 END) as benign_count,
      SUM(CASE WHEN prediction = 'VUS' THEN 1 ELSE 0 END) as vus_count,
      ROUND(AVG(confidence)::numeric, 4)::float as avg_confidence,
      MAX(created_at) as last_result_date
    FROM variant_results
    WHERE patient_id = $1 AND is_deleted = false;
    `,
    [patientId]
  );

  return {
    total: result?.total || 0,
    pathogenic_count: result?.pathogenic_count || 0,
    benign_count: result?.benign_count || 0,
    vus_count: result?.vus_count || 0,
    avg_confidence: result?.avg_confidence || 0,
    last_result_date: result?.last_result_date || null,
  };
}
