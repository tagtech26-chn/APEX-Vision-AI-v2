export const API: string = (
    (import.meta.env.VITE_API_BASE as string | undefined) ?? ""
).replace(/\/+$/, "");
