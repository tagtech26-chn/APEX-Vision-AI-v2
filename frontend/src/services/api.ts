import axios, { AxiosError } from "axios";

import { API } from "../config";

export const api = axios.create({
    baseURL: API,
    headers: { "Content-Type": "application/json" },
    timeout: 30_000,
});

const RETRYABLE_STATUS = new Set([408, 425, 429, 502, 503, 504]);
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function getWithRetry<T>(url: string, attempts = 3): Promise<T> {
    let lastError: unknown;
    for (let attempt = 0; attempt < attempts; attempt += 1) {
        try {
            const { data } = await api.get<T>(url);
            return data;
        } catch (error) {
            lastError = error;
            const axiosError = error as AxiosError;
            const status = axiosError.response?.status;
            const retryable = !axiosError.response || (status !== undefined && RETRYABLE_STATUS.has(status));
            if (!retryable || attempt === attempts - 1) break;
            await sleep(250 * 2 ** attempt);
        }
    }
    throw lastError instanceof Error ? lastError : new Error("Request failed");
}

export interface Room { id: number; name: string; image: string; thumbnail: string; }
export interface Tile {
    id: number; name: string; category: string; finish: string; size: string;
    series: string; image: string; imageUrl: string; thumbnail: string;
}
export interface RenderRequest {
    room: number; tile: number; tile_size: number; grout_width: number;
    grout_color: number[]; pattern: string;
}

export async function getRooms(): Promise<Room[]> { return getWithRetry("/api/rooms"); }
export async function getCategories(): Promise<string[]> { return getWithRetry("/api/catalog/categories"); }
export async function getFinishes(): Promise<string[]> { return getWithRetry("/api/catalog/finishes"); }
export async function getSizes(): Promise<string[]> { return getWithRetry("/api/catalog/sizes"); }
export async function getSeries(): Promise<string[]> { return getWithRetry("/api/catalog/series"); }
export async function getTiles(): Promise<Tile[]> { return getWithRetry("/api/catalog/tiles"); }

export interface RenderJob {
    job_id: string;
    status: "queued" | "processing" | "superseded" | "done" | "error";
    progress: number;
    message: string;
    image?: string;
    filename?: string;
    duration_seconds?: number;
}

export async function renderScene(request: RenderRequest): Promise<RenderJob> {
    const { data } = await api.post<RenderJob>("/api/render", request);
    return data;
}

export async function getRenderStatus(jobId: string): Promise<RenderJob> {
    return getWithRetry<RenderJob>(`/api/render/${encodeURIComponent(jobId)}`);
}

const POLL_INTERVAL_MS = 1500;
const POLL_TIMEOUT_MS = 6 * 60 * 1000;

export async function submitAndWaitRender(
    request: RenderRequest,
    onProgress?: (job: RenderJob) => void,
): Promise<RenderJob> {
    const { job_id } = await renderScene(request);
    const deadline = Date.now() + POLL_TIMEOUT_MS;

    while (Date.now() < deadline) {
        await sleep(POLL_INTERVAL_MS);
        const job = await getRenderStatus(job_id);
        onProgress?.(job);
        if (job.status === "done" || job.status === "error" || job.status === "superseded") {
            return job;
        }
    }

    throw new Error("Render timed out. The server may still be processing the job.");
}
