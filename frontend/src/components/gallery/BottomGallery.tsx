import { useCallback, useEffect, useState } from "react";
import { Box, CircularProgress, IconButton, TextField, Typography } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import TileGrid from "./TileGrid";
import { getCategories, getFinishes } from "../../services/api";
import { useRenderStore } from "../../store/renderStore";

export default function BottomGallery() {
    const [expanded, setExpanded] = useState(true);
    const [categories, setCategories] = useState<string[]>([]);
    const [finishes, setFinishes] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);

    const search = useRenderStore((s) => s.search);
    const category = useRenderStore((s) => s.category);
    const finish = useRenderStore((s) => s.finish);
    const setSearch = useRenderStore((s) => s.setSearch);
    const setCategory = useRenderStore((s) => s.setCategory);
    const setFinish = useRenderStore((s) => s.setFinish);

    const loadFilters = useCallback(async () => {
        try {
            const [cats, fins] = await Promise.all([getCategories(), getFinishes()]);
            setCategories(cats);
            setFinishes(fins);
        } catch (error) {
            console.error("Catalog filters unavailable", error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { void loadFilters(); }, [loadFilters]);

    const chips = ["All", ...categories].filter((value, index, list) => list.indexOf(value) === index).slice(0, 9);

    return (
        <Box sx={{ position: "absolute", left: { xs: 0, md: 212 }, right: { xs: 0, md: 0 }, bottom: 0, height: expanded ? 274 : 54, transition: "height .25s ease", bgcolor: "#0b1118", borderTop: "1px solid #202b38", zIndex: 1200, overflow: "hidden", boxShadow: "0 -12px 30px rgba(0,0,0,.28)" }}>
            <Box sx={{ height: 54, display: "flex", alignItems: "center", gap: 1.5, px: 2, borderBottom: "1px solid #1c2733" }}>
                <IconButton size="small" onClick={() => setExpanded((v) => !v)} sx={{ color: "#aab5c2" }}>{expanded ? <ExpandMoreIcon /> : <ExpandLessIcon />}</IconButton>
                <Typography sx={{ color: "#f4f6fa", fontSize: 15, fontWeight: 800 }}>Material Catalog</Typography>
                <Box sx={{ display: "flex", gap: .75, ml: 1, overflow: "hidden" }}>
                    {chips.map((item) => {
                        const selected = item === "All" ? category === "" : category === item;
                        return <Box key={item} component="button" onClick={() => setCategory(item === "All" ? "" : item)} sx={{ border: 0, borderRadius: 1, px: 1.25, py: .55, bgcolor: selected ? "#6840e8" : "#141d27", color: selected ? "#fff" : "#a4afbc", fontSize: 11, cursor: "pointer", whiteSpace: "nowrap" }}>{item}</Box>;
                    })}
                </Box>
                <Box sx={{ ml: "auto", width: { xs: 180, sm: 250 }, display: "flex", alignItems: "center", gap: .5 }}>
                    <SearchIcon sx={{ color: "#687686", fontSize: 19 }} />
                    <TextField value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search materials..." variant="standard" fullWidth InputProps={{ disableUnderline: true }} sx={{ "& input": { color: "#dbe2ea", fontSize: 12 }, "& input::placeholder": { color: "#697789", opacity: 1 } }} />
                </Box>
            </Box>
            {expanded && <Box sx={{ height: 220, overflow: "hidden", px: 1, pt: 1 }}>
                <Box sx={{ display: "flex", gap: .75, px: 1, mb: 1, overflowX: "auto" }}>
                    {finishes.slice(0, 7).map((item) => <Box key={item} component="button" onClick={() => setFinish(finish === item ? "" : item)} sx={{ border: "1px solid", borderColor: finish === item ? "#6840e8" : "#25313e", borderRadius: 1, px: 1, py: .4, bgcolor: finish === item ? "rgba(104,64,232,.18)" : "transparent", color: finish === item ? "#bdaeff" : "#7f8b99", fontSize: 10, cursor: "pointer", whiteSpace: "nowrap" }}>{item}</Box>)}
                </Box>
                {loading ? <Box sx={{ display: "flex", justifyContent: "center", pt: 5 }}><CircularProgress size={22} /></Box> : <TileGrid onSelectTile={() => undefined} />}
            </Box>}
        </Box>
    );
}