// Oak REST API routes for variant results
import { Router } from "oak";
import {
  createVariantResult,
  getVariantResult,
  updateVariantResult,
  softDeleteVariantResult,
  listPatientVariantResults,
  getVariantResultAuditLog,
  getPatientAuditLog,
  getPredictionStatistics,
} from "./repository.ts";

const router = new Router();

/**
 * POST /patients/{patient_id}/variant-results - Create result
 */
router.post(
  "/patients/:patient_id/variant-results",
  async (ctx) => {
    try {
      const patientId = ctx.params.patient_id;
      const userId = ctx.request.headers.get("x-user-id") || "system";
      const body = await ctx.request.body({ type: "json" }).value;

      if (!body.prediction || body.confidence === undefined) {
        ctx.response.status = 400;
        ctx.response.body = {
          error: "Missing required fields: prediction, confidence",
        };
        return;
      }

      const result = await createVariantResult(patientId, body, userId);

      ctx.response.status = 201;
      ctx.response.body = { result };
    } catch (error) {
      console.error("Error creating variant result:", error);
      ctx.response.status = 500;
      ctx.response.body = { error: error.message };
    }
  }
);

/**
 * GET /patients/{patient_id}/variant-results - List with filtering
 */
router.get("/patients/:patient_id/variant-results", async (ctx) => {
  try {
    const patientId = ctx.params.patient_id;
    const limit = parseInt(ctx.request.url.searchParams.get("limit") || "20");
    const offset = parseInt(ctx.request.url.searchParams.get("offset") || "0");
    const startDate = ctx.request.url.searchParams.get("start_date");
    const endDate = ctx.request.url.searchParams.get("end_date");
    const prediction = ctx.request.url.searchParams.get("prediction");
    const modelVersion = ctx.request.url.searchParams.get("model_version");
    const includeDeleted =
      ctx.request.url.searchParams.get("include_deleted") === "true";
    const sortBy = ctx.request.url.searchParams.get("sort_by") || "created_at";
    const sortOrder =
      ctx.request.url.searchParams.get("sort_order") || "DESC";

    const response = await listPatientVariantResults(patientId, {
      limit,
      offset,
      start_date: startDate,
      end_date: endDate,
      prediction: prediction as any,
      model_version: modelVersion,
      include_deleted: includeDeleted,
      sort_by: sortBy as any,
      sort_order: sortOrder as any,
    });

    ctx.response.status = 200;
    ctx.response.body = response;
  } catch (error) {
    console.error("Error listing variant results:", error);
    ctx.response.status = 500;
    ctx.response.body = { error: error.message };
  }
});

/**
 * GET /patients/{patient_id}/variant-results/{result_id} - Get single result
 */
router.get(
  "/patients/:patient_id/variant-results/:result_id",
  async (ctx) => {
    try {
      const resultId = ctx.params.result_id;
      const patientId = ctx.params.patient_id;

      const result = await getVariantResult(resultId);

      if (!result) {
        ctx.response.status = 404;
        ctx.response.body = { error: "Result not found" };
        return;
      }

      if (result.patient_id !== patientId) {
        ctx.response.status = 403;
        ctx.response.body = { error: "Access denied" };
        return;
      }

      ctx.response.status = 200;
      ctx.response.body = { result };
    } catch (error) {
      console.error("Error getting variant result:", error);
      ctx.response.status = 500;
      ctx.response.body = { error: error.message };
    }
  }
);

/**
 * PUT /patients/{patient_id}/variant-results/{result_id} - Update result
 */
router.put(
  "/patients/:patient_id/variant-results/:result_id",
  async (ctx) => {
    try {
      const resultId = ctx.params.result_id;
      const patientId = ctx.params.patient_id;
      const userId = ctx.request.headers.get("x-user-id") || "system";

      const existing = await getVariantResult(resultId);

      if (!existing) {
        ctx.response.status = 404;
        ctx.response.body = { error: "Result not found" };
        return;
      }

      if (existing.patient_id !== patientId) {
        ctx.response.status = 403;
        ctx.response.body = { error: "Access denied" };
        return;
      }

      const body = await ctx.request.body({ type: "json" }).value;
      const result = await updateVariantResult(resultId, body, userId);

      ctx.response.status = 200;
      ctx.response.body = { result };
    } catch (error) {
      console.error("Error updating variant result:", error);
      ctx.response.status = 500;
      ctx.response.body = { error: error.message };
    }
  }
);

/**
 * DELETE /patients/{patient_id}/variant-results/{result_id} - Soft delete
 */
router.delete(
  "/patients/:patient_id/variant-results/:result_id",
  async (ctx) => {
    try {
      const resultId = ctx.params.result_id;
      const patientId = ctx.params.patient_id;
      const userId = ctx.request.headers.get("x-user-id") || "system";

      const result = await getVariantResult(resultId);

      if (!result) {
        ctx.response.status = 404;
        ctx.response.body = { error: "Result not found" };
        return;
      }

      if (result.patient_id !== patientId) {
        ctx.response.status = 403;
        ctx.response.body = { error: "Access denied" };
        return;
      }

      await softDeleteVariantResult(resultId, userId);

      ctx.response.status = 204;
    } catch (error) {
      console.error("Error deleting variant result:", error);
      ctx.response.status = 500;
      ctx.response.body = { error: error.message };
    }
  }
);

/**
 * GET /patients/{patient_id}/variant-results/{result_id}/audit - Audit log
 */
router.get(
  "/patients/:patient_id/variant-results/:result_id/audit",
  async (ctx) => {
    try {
      const resultId = ctx.params.result_id;
      const patientId = ctx.params.patient_id;
      const limit = parseInt(ctx.request.url.searchParams.get("limit") || "50");
      const offset = parseInt(ctx.request.url.searchParams.get("offset") || "0");

      const result = await getVariantResult(resultId);

      if (!result) {
        ctx.response.status = 404;
        ctx.response.body = { error: "Result not found" };
        return;
      }

      if (result.patient_id !== patientId) {
        ctx.response.status = 403;
        ctx.response.body = { error: "Access denied" };
        return;
      }

      const auditLog = await getVariantResultAuditLog(resultId, limit, offset);

      ctx.response.status = 200;
      ctx.response.body = auditLog;
    } catch (error) {
      console.error("Error getting audit log:", error);
      ctx.response.status = 500;
      ctx.response.body = { error: error.message };
    }
  }
);

/**
 * GET /patients/{patient_id}/audit - Patient audit log
 */
router.get("/patients/:patient_id/audit", async (ctx) => {
  try {
    const patientId = ctx.params.patient_id;
    const limit = parseInt(ctx.request.url.searchParams.get("limit") || "50");
    const offset = parseInt(ctx.request.url.searchParams.get("offset") || "0");
    const startDate = ctx.request.url.searchParams.get("start_date");
    const endDate = ctx.request.url.searchParams.get("end_date");

    const auditLog = await getPatientAuditLog(
      patientId,
      limit,
      offset,
      startDate,
      endDate
    );

    ctx.response.status = 200;
    ctx.response.body = auditLog;
  } catch (error) {
    console.error("Error getting patient audit log:", error);
    ctx.response.status = 500;
    ctx.response.body = { error: error.message };
  }
});

/**
 * GET /patients/{patient_id}/statistics - Prediction statistics
 */
router.get("/patients/:patient_id/statistics", async (ctx) => {
  try {
    const patientId = ctx.params.patient_id;
    const statistics = await getPredictionStatistics(patientId);

    ctx.response.status = 200;
    ctx.response.body = { statistics };
  } catch (error) {
    console.error("Error getting statistics:", error);
    ctx.response.status = 500;
    ctx.response.body = { error: error.message };
  }
});

export default router;
