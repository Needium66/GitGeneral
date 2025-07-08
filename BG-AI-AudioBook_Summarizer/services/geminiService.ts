
import { GoogleGenAI } from "@google/genai";

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  throw new Error("API_KEY environment variable not set");
}

const ai = new GoogleGenAI({ apiKey: API_KEY });

const PROMPT = `You are a professional book summarizer and audio script writer. You have been given exclusive early access to Bill Gates' new memoir, "Source Code". Your task is to write a compelling, narrative-driven script for a 10-minute audio summary. A 10-minute audio is approximately 1500 words.

The tone should be insightful, respectful, and engaging, capturing the essence of Bill Gates' voice and perspective as if he were narrating his own story. The summary should be structured chronologically and thematically, covering the following key aspects of his life:

1.  **Early Life and "Source Code":** Touch upon his childhood, his fascination with computers, his relationship with Paul Allen, and how these formative years became the "source code" for his life's work.
2.  **The Microsoft Era:** Detail the founding of Microsoft, the key decisions that led to its dominance (like the deal with IBM for MS-DOS), the development of Windows, and the intense culture of the company's early days.
3.  **Transition to Philanthropy:** Describe the pivot from Microsoft to the Bill & Melinda Gates Foundation. Explain the motivations behind this shift and the foundation's primary goals in global health and education.
4.  **Current Perspectives and Future Outlook:** Conclude with his current focus on major global challenges like climate change and future pandemics, and his vision for the future of technology and humanity.

Please write the entire summary as a single block of text, without any headers, markdown, or section breaks, ready to be read aloud for an audio recording. Ensure the word count is close to 1500 words.`;


export const generateBookSummary = async (): Promise<string> => {
  try {
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash-preview-04-17",
      contents: PROMPT,
    });

    return response.text;
  } catch (error) {
    console.error("Error generating content from Gemini:", error);
    if (error instanceof Error) {
        throw new Error(`Gemini API call failed: ${error.message}`);
    }
    throw new Error("An unexpected error occurred while calling the Gemini API.");
  }
};
