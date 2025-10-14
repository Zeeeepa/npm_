
import { GoogleGenAI, Type } from "@google/genai";
// FIX: Add ProjectRepository to imports
import { NpmPackage, ProjectRepository } from "../types";

// This will be initialized with process.env.API_KEY, which is assumed to be available.
// As per instructions, no UI for key management is needed.
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
const model = "gemini-2.5-flash";

export async function discoverPackages(topic: string): Promise<{packageName: string, reason: string}[]> {
    const prompt = `
        You are an expert software developer and NPM package specialist.
        Based on the following topic, recommend up to 20 relevant NPM packages.
        For each package, provide a brief, one-sentence reason for your recommendation.
        Focus on popular, well-maintained, and high-quality packages.

        Topic: "${topic}"
    `;

    try {
        const response = await ai.models.generateContent({
            model,
            contents: prompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        packages: {
                            type: Type.ARRAY,
                            items: {
                                type: Type.OBJECT,
                                properties: {
                                    packageName: {
                                        type: Type.STRING,
                                        description: 'The exact name of the NPM package.',
                                    },
                                    reason: {
                                        type: Type.STRING,
                                        description: 'A brief, one-sentence reason for the recommendation.',
                                    },
                                },
                                required: ["packageName", "reason"],
                            },
                        },
                    },
                    required: ["packages"],
                },
            },
        });

        const jsonStr = response.text.trim();
        const parsed = JSON.parse(jsonStr);
        return parsed.packages || [];

    } catch (error) {
        console.error("Gemini API Error (discoverPackages):", error);
        throw new Error("Failed to get recommendations from Gemini API. The model may be unavailable or the API key might be invalid.");
    }
}


// FIX: Add summarizeRepository function for GitHub repos
export async function summarizeRepository(repo: ProjectRepository, filePaths: string[]): Promise<string> {
    const fileList = filePaths.slice(0, 300).join('\n'); // Limit file list
    const prompt = `
        As an expert software architect, provide a concise summary of the following GitHub repository.
        The response should be in markdown format.
        Focus on its primary purpose, the technologies it likely uses based on its file names, and its overall structure.

        Repository Name: ${repo.full_name}
        Description: ${repo.description || 'N/A'}
        Primary Language: ${repo.language || 'N/A'}

        File Structure (partial list):
        ${fileList}
    `;

    try {
        const response = await ai.models.generateContent({
            model,
            contents: prompt,
        });
        return response.text;
    } catch (error) {
        console.error("Gemini API Error (summarizeRepository):", error);
        throw new Error("Failed to get summary from Gemini API. Please check if the API key is configured correctly.");
    }
}

export async function summarizeNpmPackage(pkg: NpmPackage, filePaths: string[]): Promise<string> {
    const fileList = filePaths.slice(0, 300).join('\n'); // Limit file list to avoid overly long prompts
    const prompt = `
        As an expert software architect, provide a concise summary of the following NPM package.
        The response should be in markdown format.
        Focus on its primary purpose, the technologies it likely uses based on its dependencies and file names, and its overall structure.

        Package Name: ${pkg.name}
        Description: ${pkg.description || 'N/A'}
        Keywords: ${(pkg.keywords || []).join(', ')}

        File Structure (partial list):
        ${fileList}
    `;

    try {
        const response = await ai.models.generateContent({
            model,
            contents: prompt,
        });
        return response.text;
    } catch (error) {
        console.error("Gemini API Error (summarizeNpmPackage):", error);
        throw new Error("Failed to get summary from Gemini API. Please check if the API key is configured correctly.");
    }
}


export async function explainFile(filePath: string, fileContent: string): Promise<string> {
    // Truncate file content to avoid exceeding token limits, focusing on the beginning of the file.
    const contentSnippet = fileContent.slice(0, 15000); 

    const prompt = `
        As an expert code reviewer, provide a clear explanation of the following code file in markdown format.
        Describe its purpose, its main functions or components, and its role within a larger project.
        If it's a configuration file, explain what it configures.

        File Path: ${filePath}

        File Content:
        \`\`\`
        ${contentSnippet}
        \`\`\`
    `;

    try {
        const response = await ai.models.generateContent({
            model,
            contents: prompt,
        });
        return response.text;
    } catch (error) {
        console.error("Gemini API Error (explainFile):", error);
        throw new Error("Failed to get explanation from Gemini API.");
    }
}
