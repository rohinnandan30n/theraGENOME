// PostgreSQL connection management for Deno
import { load } from "dotenv";

// Load environment variables - gracefully handle missing .env
try {
  await load({ export: true, allowEmptyValues: true });
} catch (_error) {
  // .env file not found or missing variables - continue anyway
  console.warn("Note: .env file not found or incomplete - continuing in lightweight mode");
}

// Use a loosely-typed client so we don't force a hard dependency during local tests
let client: any = null;

/**
 * Initialize database: connect and load schemas
 */
export async function initDatabase(): Promise<void> {
  const databaseUrl = Deno.env.get("DATABASE_URL");

  // If no DATABASE_URL provided, skip DB initialization (useful for local runs/tests)
  if (!databaseUrl) {
    console.warn("DATABASE_URL not set - skipping database initialization (running in lightweight mode)");
    client = null;
    return;
  }

  try {
    // Dynamically import postgres to avoid type resolution when not needed
    const { Client } = await import("https://deno.land/x/postgres@v0.20.1/mod.ts");
    client = new Client(databaseUrl);
    await client.connect();
    console.log("✓ Connected to PostgreSQL");

    // Load and execute schema files
    const schemaFiles = [
      "src/schemas/variant_results_schema.sql",
      "src/schemas/variant_audit_log_schema.sql",
    ];

    for (const schemaFile of schemaFiles) {
      try {
        const schema = await Deno.readTextFile(schemaFile);
        await client.queryArray(schema);
        console.log(`✓ Loaded schema: ${schemaFile}`);
      } catch (error) {
        console.error(`✗ Failed to load schema ${schemaFile}:`, error);
        throw error;
      }
    }

    console.log("✓ All schemas initialized");
  } catch (error) {
    console.error("✗ Database initialization failed:", error);
    throw error;
  }
}

/**
 * Get singleton database client
 */
export function getClient(): any {
  if (!client) {
    throw new Error(
      "Database not initialized. Call initDatabase() first."
    );
  }
  return client;
}

/**
 * Close database connection
 */
export async function closeDatabase(): Promise<void> {
  if (client) {
    await client.end();
    client = null;
    console.log("✓ Database connection closed");
  }
}

/**
 * Execute query returning array of results
 */
export async function queryArray(
  sql: string,
  params?: unknown[]
): Promise<unknown[][]> {
  const c = getClient();
  return await c.queryArray(sql, params);
}

/**
 * Execute query returning objects
 */
export async function queryObject<T>(
  sql: string,
  params?: unknown[]
): Promise<T[]> {
  const c = getClient();
  const res: any = await c.queryObject(sql, params);
  return res as T[];
}

/**
 * Execute query with single result object
 */
export async function query<T>(
  sql: string,
  params?: unknown[]
): Promise<T | null> {
  const c = getClient();
  const result: any = await c.queryObject(sql, params);
  // 'result' might be a plain array depending on driver; normalize
  if (Array.isArray(result)) {
    return (result as unknown as T[])[0] || null;
  }
  return result.rows?.[0] || null;
}

/**
 * Execute transaction
 */
export async function transaction<T>(
  fn: (client: any) => Promise<T>
): Promise<T> {
  const c = getClient();
  try {
    await c.queryArray("BEGIN");
    const result = await fn(c);
    await c.queryArray("COMMIT");
    return result;
  } catch (error) {
    await c.queryArray("ROLLBACK");
    throw error;
  }
}
