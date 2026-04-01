// PostgreSQL connection management for Deno
import { Client } from "postgres";
import { load } from "dotenv";

// Load environment variables
await load({ export: true });

let client: Client | null = null;

/**
 * Initialize database: connect and load schemas
 */
export async function initDatabase(): Promise<void> {
  const databaseUrl = Deno.env.get("DATABASE_URL");
  if (!databaseUrl) {
    throw new Error(
      "DATABASE_URL environment variable is not set"
    );
  }

  try {
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
export function getClient(): Client {
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
  return await c.queryObject<T>(sql, params);
}

/**
 * Execute query with single result object
 */
export async function query<T>(
  sql: string,
  params?: unknown[]
): Promise<T | null> {
  const c = getClient();
  const result = await c.queryObject<T>(sql, params);
  return result.rows[0] || null;
}

/**
 * Execute transaction
 */
export async function transaction<T>(
  fn: (client: Client) => Promise<T>
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
