/**
 * BetterAuth server configuration.
 * Connects to the same PostgreSQL database as the FastAPI backend.
 * BetterAuth manages its own user/session/account/verification tables.
 */
import { betterAuth } from "better-auth";
import { nextCookies } from "better-auth/next-js";
import { Pool } from "pg";

export const auth = betterAuth({
  database: new Pool({
    connectionString: process.env.DATABASE_URL,
  }),

  emailAndPassword: {
    enabled: true,
    minPasswordLength: 8,
  },

  // Social providers — add client IDs via env vars when ready
  socialProviders: {
    ...(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET
      ? {
          google: {
            clientId: process.env.GOOGLE_CLIENT_ID,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET,
          },
        }
      : {}),
    ...(process.env.GITHUB_CLIENT_ID && process.env.GITHUB_CLIENT_SECRET
      ? {
          github: {
            clientId: process.env.GITHUB_CLIENT_ID,
            clientSecret: process.env.GITHUB_CLIENT_SECRET,
          },
        }
      : {}),
  },

  // Custom fields on the user table
  user: {
    additionalFields: {
      role: {
        type: "string",
        required: false,
        defaultValue: "user",
        input: true,
      },
      phone: {
        type: "string",
        required: false,
        input: true,
      },
    },
  },

  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24,      // refresh if older than 1 day
    cookieCache: {
      enabled: true,
      maxAge: 60 * 5,             // 5 min cache
    },
  },

  // Required for server actions / server components to set cookies
  plugins: [nextCookies()],
});

export type Session = typeof auth.$Infer.Session;
