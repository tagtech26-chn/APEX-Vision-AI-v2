import { useCallback, useEffect, useState } from "react";

import {
    Alert,
    Box,
    CircularProgress,
    Collapse,
    IconButton,
    Paper,
    Typography,
} from "@mui/material";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

import SearchBar from "./SearchBar";
import FilterChips from "./FilterChips";
import TileGrid from "./TileGrid";
import { getCategories, getFinishes } from "../../services/api";
import { useRenderStore } from "../../store/renderStore";

export default function BottomGallery() {
    const [expanded, setExpanded] = useState(false);
    const [categories, setCategories] = useState<string[]>([]);
    const [finishes, setFinishes] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const search = useRenderStore((s) => s.search);
    const category = useRenderStore((s) => s.category);
    const finish = useRenderStore((s) => s.finish);
    const setSearch = useRenderStore((s) => s.setSearch);
    const setCategory = useRenderStore((s) => s.setCategory);
    const setFinish = useRenderStore((s) => s.setFinish);

    const loadFilters = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [cats, fins] = await Promise.all([getCategories(), getFinishes()]);
            setCategories(cats);
            setFinishes(fins);
        } catch {
            setError("Unable to load catalog filters. Please retry.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { void loadFilters(); }, [loadFilters]);

    return (
        <Paper elevation={12} sx={{ position: "absolute", left: 0, right: 0, bottom: 0, height: expanded ? { xs: 430, sm: 470 } : 58, transition: "height .30s ease", borderTopLeftRadius: 24, borderTopRightRadius: 24, overflow: "hidden", bgcolor: "#fafafa", zIndex: 1099 }}>
            <Box sx={{ height: 58, px: { xs: 1, sm: 2 }, display: "flex", alignItems: "center", borderBottom: "1px solid #ececec", backgroundColor: "#fafafa" }}>
                <IconButton size="small" onClick={() => setExpanded(!expanded)} sx={{ mr: 1 }}>
                    {expanded ? <ExpandMoreIcon /> : <ExpandLessIcon />}
                </IconButton>
                <Typography variant="h6" sx={{ fontWeight: 700, fontSize: { xs: "1rem", sm: "1.25rem" } }}>Tile Gallery</Typography>
                {loading && <CircularProgress size={18} sx={{ ml: 2 }} />}
            </Box>

            <Collapse in={expanded} timeout={250}>
                <Box sx={{ maxHeight: { xs: 372, sm: 412 }, overflowY: "auto" }}>
                    {error && <Alert severity="error" sx={{ m: 2 }} onClose={() => setError(null)} action={<button onClick={() => void loadFilters()}>Retry</button>}>{error}</Alert>}
                    <Box sx={{ p: 2 }}><SearchBar value={search} onChange={setSearch} /></Box>
                    <Box sx={{ px: 2 }}>
                        <FilterChips title="Category" items={categories} selected={category} onSelect={setCategory} />
                        <FilterChips title="Finish" items={finishes} selected={finish} onSelect={setFinish} />
                    </Box>
                    <Box sx={{ px: 1, pb: 1 }}><TileGrid onSelectTile={() => setExpanded(false)} /></Box>
                </Box>
            </Collapse>
        </Paper>
    );
}
