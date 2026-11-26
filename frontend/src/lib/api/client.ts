import createClient from "openapi-fetch";
import type { paths } from "./generated/schema.d.ts";

/**
 * Typed API client for the WolfStreet Signal backend.
 * Base URL is proxied through Next.js rewrites to avoid CORS in development.
 * In production, set NEXT_PUBLIC_API_URL to point directly at the backend.
 */
export const apiClient = createClient<paths>({ baseUrl: "/" });

export type { paths } from "./generated/schema.d.ts";
