import { useEffect, useState } from "react";

import {
    Box,
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

import {
    getCategories,
    getFinishes,
} from "../../services/api";

import {
    useRenderStore,
} from "../../store/renderStore";

export default function BottomGallery() {

    const [expanded, setExpanded] = useState(false);

    const [categories, setCategories] = useState<string[]>([]);
    const [finishes, setFinishes] = useState<string[]>([]);

    const search = useRenderStore((s) => s.search);
    const category = useRenderStore((s) => s.category);
    const finish = useRenderStore((s) => s.finish);

    const setSearch = useRenderStore((s) => s.setSearch);
    const setCategory = useRenderStore((s) => s.setCategory);
    const setFinish = useRenderStore((s) => s.setFinish);

    useEffect(() => {
        loadFilters();
    }, []);

    async function loadFilters() {

        try {

            const [cats, fins] = await Promise.all([
                getCategories(),
                getFinishes(),
            ]);

            setCategories(cats);
            setFinishes(fins);

        } catch (err) {

            console.error(err);

        }
    }

    return (

        <Paper
            elevation={12}
            sx={{
                position: "absolute",
                left: 0,
                right: 0,
                bottom: 0,

                height: expanded ? 470 : 58,

                transition: "height .30s ease",

                borderTopLeftRadius: 24,
                borderTopRightRadius: 24,

                overflow: "hidden",

                bgcolor: "#fafafa",

                zIndex: 1099,
            }}
        >

            {/* Header */}

            <Box
                sx={{
                    height: 58,

                    px: 2,

                    display: "flex",

                    alignItems: "center",

                    borderBottom: "1px solid #ececec",

                    backgroundColor: "#fafafa",
                }}
            >

                <IconButton
                    size="small"
                    onClick={() => setExpanded(!expanded)}
                    sx={{
                        mr: 1,
                    }}
                >
                    {expanded ? (
                        <ExpandMoreIcon />
                    ) : (
                        <ExpandLessIcon />
                    )}
                </IconButton>

                <Typography
                    variant="h6"
                    sx={{ fontWeight: 700 }}
                >
                    Tile Gallery
                </Typography>

            </Box>

            <Collapse
                in={expanded}
                timeout={250}
            >

                <Box
                    sx={{
                        maxHeight: 412,
                        overflowY: "auto",
                    }}
                >

                    <Box sx={{ p: 2 }}>

                        <SearchBar
                            value={search}
                            onChange={setSearch}
                        />

                    </Box>

                    <Box sx={{ px: 2 }}>

                        <FilterChips
                            title="Category"
                            items={categories}
                            selected={category}
                            onSelect={setCategory}
                        />

                        <FilterChips
                            title="Finish"
                            items={finishes}
                            selected={finish}
                            onSelect={setFinish}
                        />

                    </Box>

                    <Box sx={{ px: 1, pb: 1 }}>

                        <TileGrid onSelectTile={() => setExpanded(false)} />

                    </Box>

                </Box>

            </Collapse>

        </Paper>

    );

}