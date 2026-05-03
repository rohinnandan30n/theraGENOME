// Entry point for Deno Variant Results API
import { Application, Router } from "oak";
import { initDatabase, closeDatabase } from "./db.ts";
import router from "./routes_app.ts";

const app = new Application();

// Environment config
const HOST = Deno.env.get("HOST") || "127.0.0.1";
const PORT = parseInt(Deno.env.get("PORT") || "3000");

// Logging middleware
app.use(async (ctx, next) => {
  const start = Date.now();
  await next();
  const ms = Date.now() - start;
  console.log(`${ctx.request.method} ${ctx.request.url} - ${ms}ms`);
});

// Error handling middleware
app.use(async (ctx, next) => {
  try {
    await next();
  } catch (error) {
    console.error("Error:", error);
    ctx.response.status = 500;
    ctx.response.body = { error: error.message };
  }
});

// CORS middleware
app.use(async (ctx, next) => {
  ctx.response.headers.set("Access-Control-Allow-Origin",
    Deno.env.get("CORS_ORIGIN") || "*"
  );
  ctx.response.headers.set(
    "Access-Control-Allow-Methods",
    "GET, POST, PUT, DELETE, OPTIONS"
  );
  ctx.response.headers.set(
    "Access-Control-Allow-Headers",
    "Content-Type, Authorization, X-User-ID"
  );

  if (ctx.request.method === "OPTIONS") {
    ctx.response.status = 204;
    return;
  }

  await next();
});

// Content-type middleware
app.use(async (ctx, next) => {
  ctx.response.headers.set("Content-Type", "application/json");
  await next();
});

// Health check endpoint
const healthRouter = new Router();
healthRouter.get("/health", (ctx) => {
  ctx.response.status = 200;
  ctx.response.body = {
    status: "healthy",
    service: "variant-results-api",
    timestamp: new Date().toISOString(),
  };
});

// Routes
app.use(healthRouter.routes());
app.use(router.routes());

// Start server
async function start() {
  try {
    console.log("🚀 Starting Variant Results API...");
    await initDatabase();

    app.listen({ hostname: HOST, port: PORT });
    console.log(`✓ Server running at http://${HOST}:${PORT}`);
  } catch (error) {
    console.error("✗ Server startup failed:", error);
    await closeDatabase();
    Deno.exit(1);
  }
}

// Graceful shutdown
Deno.addSignalListener("SIGINT", async () => {
  console.log("\n🛑 Shutting down gracefully...");
  await closeDatabase();
  Deno.exit(0);
});

start();
