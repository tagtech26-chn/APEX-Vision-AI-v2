import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Box, Card, CardActionArea, CardContent, CircularProgress, Typography } from "@mui/material";
import { getTiles, submitAndWaitRender } from "../../services/api";
import type { Tile } from "../../services/api";
import { useRenderStore } from "../../store/renderStore";
import { API } from "../../config";

export default function TileGrid({ onSelectTile }: { onSelectTile?: () => void }) {
    const [tiles, setTiles] = useState<Tile[]>([]);
    const [loading, setLoading] = useState(true);
    const initialRenderSkipped = useRef(false);

    const selectedTile = useRenderStore((s) => s.tile);
    const search = useRenderStore((s) => s.search);
    const category = useRenderStore((s) => s.category);
    const finish = useRenderStore((s) => s.finish);
    const tileSize = useRenderStore((s) => s.tileSize);
    const groutWidth = useRenderStore((s) => s.groutWidth);
    const groutColor = useRenderStore((s) => s.groutColor);
    const pattern = useRenderStore((s) => s.pattern);
    const renderNonce = useRenderStore((s) => s.renderNonce);
    const rendering = useRenderStore((s) => s.loading);
    const setTile = useRenderStore((s) => s.setTile);
    const setImage = useRenderStore((s) => s.setImage);
    const setLoadingState = useRenderStore((s) => s.setLoading);
    const setProgress = useRenderStore((s) => s.setProgress);
    const setProgressMessage = useRenderStore((s) => s.setProgressMessage);

    useEffect(() => {
        let mounted = true;
        void getTiles().then((data) => { if (mounted) setTiles(data); }).catch(console.error).finally(() => { if (mounted) setLoading(false); });
        return () => { mounted = false; };
    }, []);

    const renderTile = useCallback(async (tile: Tile) => {
        try {
            setLoadingState(true);
            setProgress(0);
            setProgressMessage("Queued for Heavy AI rendering...");
            const response = await submitAndWaitRender({
                room: useRenderStore.getState().room,
                tile: tile.id,
                tile_size: tileSize,
                grout_width: groutWidth,
                grout_color: groutColor,
                pattern,
                material_profile: "auto",
            }, (j) => {
                setProgress(j.progress ?? 0);
                setProgressMessage(j.message || j.status);
            });
            if (response.status === "done" && response.image) {
                setImage(response.image + "?t=" + Date.now());
            }
        } catch (err) {
            console.error(err);
            setProgressMessage(err instanceof Error ? err.message : "Render failed");
        } finally {
            setLoadingState(false);
        }
    }, [tileSize, groutWidth, groutColor, pattern, setLoadingState, setImage, setProgress, setProgressMessage]);

    useEffect(() => {
        if (tiles.length === 0) return;

        // The app already has an initial scene/output. Do not launch a Heavy AI
        // inference merely because the catalog mounted. A render is started by
        // an explicit tile selection or by another explicit render action.
        if (!initialRenderSkipped.current) {
            initialRenderSkipped.current = true;
            return;
        }

        const tile = tiles.find((t) => t.id === selectedTile);
        if (tile && !rendering) void renderTile(tile);
    }, [selectedTile, tiles, renderTile, renderNonce, rendering]);

    const filteredTiles = useMemo(() => tiles.filter((tile) => {
        const matchesSearch = search === "" || tile.name.toLowerCase().includes(search.toLowerCase());
        const matchesCategory = category === "" || tile.category === category;
        const matchesFinish = finish === "" || tile.finish === finish;
        return matchesSearch && matchesCategory && matchesFinish;
    }), [tiles, search, category, finish]);

    function selectTile(tile: Tile) {
        if (rendering) return;
        setTile(tile.id);
        onSelectTile?.();
    }

    if (loading) return <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", height: 160 }}><CircularProgress size={24} /></Box>;

    return (
        <Box sx={{ display: "flex", gap: 1.5, overflowX: "auto", px: 1, pb: 1.5, scrollbarWidth: "thin" }}>
            {filteredTiles.map((tile) => (
                <Card key={tile.id} elevation={0} sx={{ minWidth: 138, maxWidth: 160, flexShrink: 0, cursor: rendering ? "wait" : "pointer", bgcolor: "#111923", border: selectedTile === tile.id ? "2px solid #7447ff" : "1px solid #263241", borderRadius: 1.5, overflow: "hidden", transition: ".2s", "&:hover": { transform: rendering ? "none" : "translateY(-3px)", borderColor: "#7447ff" } }}>
                    <CardActionArea disabled={rendering} onClick={() => selectTile(tile)}>
                        <CardMedia component="img" height="92" image={`${API}${tile.thumbnail}`} alt={tile.name} sx={{ objectFit: "cover" }} onError={(e) => { (e.target as HTMLImageElement).src = "https://placehold.co/180x120?text=Tile"; }} />
                        <CardContent sx={{ p: 1.25, "&:last-child": { pb: 1.25 } }}>
                            <Typography sx={{ fontWeight: 700, color: "#f5f7fb", fontSize: 12 }} noWrap>{tile.name}</Typography>
                            <Typography sx={{ color: "#8d9aaa", fontSize: 10, mt: .25 }} noWrap>{tile.category} · {tile.finish}</Typography>
                            <Typography sx={{ color: "#697789", fontSize: 10 }} noWrap>{tile.size}</Typography>
                        </CardContent>
                    </CardActionArea>
                </Card>
            ))}
            {filteredTiles.length === 0 && <Typography sx={{ color: "#8995a4", p: 3 }}>No materials found.</Typography>}
        </Box>
    );
}