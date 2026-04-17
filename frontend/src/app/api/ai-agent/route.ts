import { streamText, tool, convertToModelMessages } from "ai";
import { createGroq } from "@ai-sdk/groq";
import { z } from "zod";

const groq = createGroq({
  apiKey: process.env.GROQ_API_KEY,
});

const SYSTEM_PROMPT = `You are the StayNest travel assistant — a friendly, knowledgeable AI that helps users find vacation rental properties and plan trips.

You can:
- Search for available properties by city, price range, guest capacity, and dates using the search_properties tool.
- Generate personalised travel itineraries using the generate_itinerary tool.

When presenting search results, format them clearly with property names, prices, locations, and links when available.
When generating itineraries, organise them day-by-day with activities, dining suggestions, and travel tips.

Always be helpful, concise, and enthusiastic about travel!`;

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();

    const result = streamText({
      model: groq("llama-3.3-70b-versatile"),
      system: SYSTEM_PROMPT,
      messages: await convertToModelMessages(messages),
      tools: {
      search_properties: tool({
        description:
          "Search for available StayNest rental properties based on filters like city, price range, guest capacity, and dates.",
        inputSchema: z.object({
          city: z.string().optional().describe("City to search in"),
          min_price: z.number().optional().describe("Minimum price per night"),
          max_price: z.number().optional().describe("Maximum price per night"),
          max_guests: z.number().optional().describe("Maximum guest capacity"),
          check_in: z
            .string()
            .optional()
            .describe("Check-in date in ISO 8601 format"),
          check_out: z
            .string()
            .optional()
            .describe("Check-out date in ISO 8601 format"),
          page: z.number().default(1).describe("Page number for pagination"),
        }),
        execute: async (params) => {
          const apiUrl =
            process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL;
          const url = new URL(`${apiUrl}/properties`);
          for (const [key, value] of Object.entries(params)) {
            if (value !== undefined) {
              url.searchParams.set(key, String(value));
            }
          }
          const res = await fetch(url.toString());
          if (!res.ok) {
            return { error: `Property search failed: ${res.status}` };
          }
          return await res.json();
        },
      }),
      generate_itinerary: tool({
        description:
          "Generate a travel itinerary for a destination. The model will create a detailed day-by-day plan.",
        inputSchema: z.object({
          destination: z.string().describe("Travel destination"),
          days: z.number().describe("Number of days for the trip"),
          interests: z
            .array(z.string())
            .optional()
            .describe("Traveller interests, e.g. food, hiking, museums"),
        }),
        execute: async ({ destination, days, interests }) => {
          return {
            destination,
            days,
            interests: interests ?? [],
            note: "Itinerary generation triggered — please provide the day-by-day plan based on these parameters.",
          };
        },
      }),
    },
  });

  return result.toUIMessageStreamResponse();
  } catch (error) {
    console.error("[ai-agent] Error:", error);
    return new Response(
      JSON.stringify({ error: "AI agent failed to respond" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}
