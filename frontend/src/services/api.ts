import axios from "axios";

import { API } from "../config";

export const api = axios.create({
    baseURL: API,
    headers: {
        "Content-Type": "application/json",
    },
});

export interface Room {

    id: number;

    name: string;

    image: string;

    thumbnail: string;

}

export interface Tile {

    id: number;

    name: string;

    category: string;

    finish: string;

    size: string;

    series: string;

    image: string;

    imageUrl: string;

    thumbnail: string;

}

export interface RenderRequest {

    room: number;

    tile: number;

    tile_size: number;

    grout_width: number;

    grout_color: number[];

    pattern: string;

}

export async function getRooms(): Promise<Room[]> {

    const { data } = await api.get("/api/rooms");

    return data;

}

export async function getCategories(): Promise<string[]> {

    const { data } = await api.get("/api/catalog/categories");

    return data;

}

export async function getFinishes(): Promise<string[]> {

    const { data } = await api.get("/api/catalog/finishes");

    return data;

}

export async function getSizes(): Promise<string[]> {

    const { data } = await api.get("/api/catalog/sizes");

    return data;

}

export async function getSeries(): Promise<string[]> {

    const { data } = await api.get("/api/catalog/series");

    return data;

}

export async function getTiles(): Promise<Tile[]> {

    const { data } = await api.get("/api/catalog/tiles");

    return data;

}

export interface RenderJob {

    job_id: string;

    status: "queued" | "processing" | "superseded" | "done" | "error";

    progress: number;

    message: string;

    image?: string;

    filename?: string;

}

export async function renderScene(request: RenderRequest): Promise<RenderJob> {

    const { data } = await api.post("/api/render", request);

    return data;

}

export async function getRenderStatus(jobId: string): Promise<RenderJob> {

    const { data } = await api.get(`/api/render/${jobId}`);

    return data;

}

const POLL_INTERVAL_MS = 1500;
const POLL_TIMEOUT_MS = 6 * 60 * 1000;

export async function submitAndWaitRender(
    request: RenderRequest,
    onProgress?: (job: RenderJob) => void
): Promise<RenderJob> {

    const { job_id } = await renderScene(request);

    const deadline = Date.now() + POLL_TIMEOUT_MS;

    while (Date.now() < deadline) {

        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));

        const job = await getRenderStatus(job_id);

        onProgress?.(job);

        if (job.status === "done" || job.status === "error" || job.status === "superseded") {

            return job;

        }

    }

    throw new Error("Render timed out");

}