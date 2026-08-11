import { create } from "zustand";

export interface RenderStore {
    room: number;
    roomName: string;
    roomDialogOpen: boolean;
    tile: number;
    tileSize: number;
    pattern: string;
    category: string;
    finish: string;
    size: string;
    series: string;
    search: string;
    groutWidth: number;
    groutColor: number[];
    image: string;
    loading: boolean;
    progress: number;
    progressMessage: string;
    panelOpen: boolean;
    renderNonce: number;

    setRoom: (id: number) => void;
    setRoomName: (name: string) => void;
    setRoomDialogOpen: (open: boolean) => void;
    setTile: (id: number) => void;
    setTileSize: (size: number) => void;
    setPattern: (pattern: string) => void;
    setImage: (image: string) => void;
    setLoading: (loading: boolean) => void;
    setProgress: (progress: number) => void;
    setProgressMessage: (message: string) => void;
    setPanelOpen: (open: boolean) => void;
    setCategory: (category: string) => void;
    setFinish: (finish: string) => void;
    setSize: (size: string) => void;
    setSeries: (series: string) => void;
    setSearch: (search: string) => void;
    setGroutWidth: (width: number) => void;
    setGroutColor: (color: number[]) => void;
    requestRender: () => void;
}

export const useRenderStore = create<RenderStore>((set) => ({
    room: 1,
    roomName: "Living Room",
    roomDialogOpen: false,
    tile: 1,
    tileSize: 600,
    pattern: "Straight",
    category: "",
    finish: "",
    size: "",
    series: "",
    search: "",
    groutWidth: 2,
    groutColor: [220, 220, 220],
    image: "/output/room_render.png?t=" + Date.now(),
    loading: false,
    progress: 0,
    progressMessage: "",
    panelOpen: false,
    renderNonce: 0,

    setRoom: (id) => set({ room: id }),
    setRoomName: (name) => set({ roomName: name }),
    setRoomDialogOpen: (open) => set({ roomDialogOpen: open }),
    setTile: (id) => set({ tile: id }),
    setTileSize: (size) => set({ tileSize: size }),
    setPattern: (pattern) => set({ pattern }),
    setImage: (image) => set({ image }),
    setLoading: (loading) => set({ loading }),
    setProgress: (progress) => set({ progress }),
    setProgressMessage: (message) => set({ progressMessage: message }),
    setPanelOpen: (open) => set({ panelOpen: open }),
    setCategory: (category) => set({ category }),
    setFinish: (finish) => set({ finish }),
    setSize: (size) => set({ size }),
    setSeries: (series) => set({ series }),
    setSearch: (search) => set({ search }),
    setGroutWidth: (width) => set({ groutWidth: width }),
    setGroutColor: (color) => set({ groutColor: color }),
    requestRender: () => set((state) => ({ renderNonce: state.renderNonce + 1 })),
}));