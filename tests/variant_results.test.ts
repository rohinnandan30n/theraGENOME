// Deno tests for variant results repository
import { assertEquals, assert } from "https://deno.land/std@0.208.0/testing/asserts.ts";
import {
  createVariantResult,
  getVariantResult,
  updateVariantResult,
  softDeleteVariantResult,
  listPatientVariantResults,
  getPredictionStatistics,
} from "../repository.ts";

const TEST_PATIENT_ID = "550e8400-e29b-41d4-a716-446655440000";
const TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440001";

const SAMPLE_VARIANT_RESULT = {
  variant_id: "rs123456",
  chrom: "17",
  pos: 41244394,
  ref: "T",
  alt: "G",
  prediction: "Pathogenic" as const,
  confidence: 0.87,
  probabilities: { benign: 0.13, pathogenic: 0.87 },
  model_version: "v2",
  feature_importance: { feature1: 0.45, feature2: 0.32 },
  clinical_notes: "Test variant",
  metadata: { source: "test" },
};

Deno.test("createVariantResult - should create and return variant result", async () => {
  const result = await createVariantResult(
    TEST_PATIENT_ID,
    SAMPLE_VARIANT_RESULT,
    TEST_USER_ID
  );

  assert(result.result_id !== undefined);
  assertEquals(result.patient_id, TEST_PATIENT_ID);
  assertEquals(result.prediction, "Pathogenic");
  assertEquals(result.confidence, 0.87);
  assertEquals(result.is_deleted, false);
});

Deno.test("getVariantResult - should retrieve variant result", async () => {
  const created = await createVariantResult(
    TEST_PATIENT_ID,
    SAMPLE_VARIANT_RESULT,
    TEST_USER_ID
  );

  const retrieved = await getVariantResult(created.result_id!);

  assert(retrieved !== null);
  assertEquals(retrieved!.result_id, created.result_id);
  assertEquals(retrieved!.prediction, "Pathogenic");
});

Deno.test("updateVariantResult - should update variant result", async () => {
  const created = await createVariantResult(
    TEST_PATIENT_ID,
    SAMPLE_VARIANT_RESULT,
    TEST_USER_ID
  );

  const updated = await updateVariantResult(
    created.result_id!,
    {
      prediction: "Benign",
      clinical_notes: "Updated notes",
    },
    TEST_USER_ID
  );

  assertEquals(updated.prediction, "Benign");
  assertEquals(updated.clinical_notes, "Updated notes");
});

Deno.test("softDeleteVariantResult - should soft delete variant result", async () => {
  const created = await createVariantResult(
    TEST_PATIENT_ID,
    SAMPLE_VARIANT_RESULT,
    TEST_USER_ID
  );

  await softDeleteVariantResult(created.result_id!, TEST_USER_ID);

  const retrieved = await getVariantResult(created.result_id!);
  assertEquals(retrieved, null);
});

Deno.test("listPatientVariantResults - should list variant results with pagination", async () => {
  // Create test variants
  await createVariantResult(
    TEST_PATIENT_ID,
    SAMPLE_VARIANT_RESULT,
    TEST_USER_ID
  );
  await createVariantResult(
    TEST_PATIENT_ID,
    { ...SAMPLE_VARIANT_RESULT, prediction: "Benign" },
    TEST_USER_ID
  );
  await createVariantResult(
    TEST_PATIENT_ID,
    { ...SAMPLE_VARIANT_RESULT, prediction: "VUS" },
    TEST_USER_ID
  );

  const result = await listPatientVariantResults(TEST_PATIENT_ID, {
    limit: 10,
    offset: 0,
  });

  assert(result.data.length >= 3);
  assert(result.total >= 3);
  assertEquals(result.limit, 10);
  assertEquals(result.offset, 0);
});

Deno.test("listPatientVariantResults - should filter by prediction", async () => {
  // Clear and create test variants
  await createVariantResult(
    TEST_PATIENT_ID,
    { ...SAMPLE_VARIANT_RESULT, prediction: "Pathogenic" },
    TEST_USER_ID
  );
  await createVariantResult(
    TEST_PATIENT_ID,
    { ...SAMPLE_VARIANT_RESULT, prediction: "Benign" },
    TEST_USER_ID
  );

  const result = await listPatientVariantResults(TEST_PATIENT_ID, {
    prediction: "Pathogenic",
    limit: 10,
    offset: 0,
  });

  const pathogenicCount = result.data.filter(
    (r) => r.prediction === "Pathogenic"
  ).length;
  assert(pathogenicCount >= 1);
});

Deno.test("listPatientVariantResults - should handle pagination", async () => {
  // Create multiple variants
  for (let i = 0; i < 5; i++) {
    await createVariantResult(
      TEST_PATIENT_ID,
      { ...SAMPLE_VARIANT_RESULT, variant_id: `rs${i}` },
      TEST_USER_ID
    );
  }

  const page1 = await listPatientVariantResults(TEST_PATIENT_ID, {
    limit: 2,
    offset: 0,
  });

  const page2 = await listPatientVariantResults(TEST_PATIENT_ID, {
    limit: 2,
    offset: 2,
  });

  assert(page1.data.length <= 2);
  assert(page2.data.length <= 2);
  assert(page1.has_next || page1.total <= 2);
});

Deno.test("getPredictionStatistics - should return statistics", async () => {
  // Create variants with different predictions
  await createVariantResult(
    TEST_PATIENT_ID,
    { ...SAMPLE_VARIANT_RESULT, prediction: "Pathogenic", confidence: 0.9 },
    TEST_USER_ID
  );
  await createVariantResult(
    TEST_PATIENT_ID,
    { ...SAMPLE_VARIANT_RESULT, prediction: "Benign", confidence: 0.8 },
    TEST_USER_ID
  );
  await createVariantResult(
    TEST_PATIENT_ID,
    { ...SAMPLE_VARIANT_RESULT, prediction: "VUS", confidence: 0.5 },
    TEST_USER_ID
  );

  const stats = await getPredictionStatistics(TEST_PATIENT_ID);

  assert(stats.total >= 3);
  assert(stats.pathogenic_count >= 1);
  assert(stats.benign_count >= 1);
  assert(stats.vus_count >= 1);
  assert(stats.avg_confidence > 0);
  assert(stats.last_result_date !== null);
});
