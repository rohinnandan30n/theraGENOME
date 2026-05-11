// Integration tests for Deno Variant Results API
import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";

const BASE_URL = "http://127.0.0.1:8001";

// Helper function to make HTTP requests
async function makeRequest(
  method: string,
  path: string,
  body?: Record<string, unknown>
): Promise<{ status: number; data: Record<string, unknown> }> {
  try {
    const options: RequestInit = {
      method,
      headers: { "Content-Type": "application/json" },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${BASE_URL}${path}`, options);
    const data = await response.json();

    return {
      status: response.status,
      data: data as Record<string, unknown>,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`Request failed: ${message}`);
    throw error;
  }
}

// Test 1: GET /health endpoint returns 200 with correct structure
Deno.test("GET /health endpoint returns 200 with status ok, timestamp, and version", async () => {
  const response = await makeRequest("GET", "/health");

  assertEquals(response.status, 200, "Health endpoint should return 200");
  assertEquals(
    response.data.status,
    "ok",
    "Health response should have status: ok"
  );
  assertExists(
    response.data.timestamp,
    "Health response should have timestamp"
  );
  assertExists(response.data.version, "Health response should have version");

  // Verify timestamp is ISO string
  const timestamp = response.data.timestamp as string;
  const isoRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/;
  assertEquals(
    isoRegex.test(timestamp),
    true,
    "Timestamp should be ISO format"
  );
});

// Test 2: POST /variant/analyze with valid body returns 200 and has classification field
Deno.test("POST /variant/analyze with valid body returns 200 with classification", async () => {
  const validBody = {
    chrom: "17",
    pos: 41244394,
    ref: "T",
    alt: "G",
  };

  const response = await makeRequest("POST", "/variant/analyze", validBody);

  assertEquals(
    response.status,
    200,
    "Valid POST should return 200"
  );
  assertExists(
    response.data.classification,
    "Response should have classification field"
  );
  assertEquals(
    typeof response.data.classification,
    "string",
    "Classification should be a string"
  );

  // Verify other expected fields
  assertExists(response.data.confidence, "Should have confidence");
  assertExists(response.data.variant, "Should have variant");
  assertExists(response.data.timestamp, "Should have timestamp");
});

// Test 3: POST /variant/analyze with missing required field returns 422
Deno.test("POST /variant/analyze with missing required field returns 422", async () => {
  const invalidBody = {
    chrom: "17",
    pos: 41244394,
    // Missing 'ref' and 'alt' - required fields
  };

  const response = await makeRequest("POST", "/variant/analyze", invalidBody);

  assertEquals(
    response.status,
    422,
    "POST with missing fields should return 422"
  );
  assertExists(response.data.error, "Error response should have error field");
  assertEquals(
    typeof response.data.error,
    "string",
    "Error should be a string"
  );
});
