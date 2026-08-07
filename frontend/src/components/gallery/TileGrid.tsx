import { useCallback, useEffect, useMemo, useState } from "react";

import {
    Box,
    Card,
    CardActionArea,
    CardContent,
    CardMedia,
    CircularProgress,
    Typography,
} from "@mui/material";

import {
    getTiles,
    submitAndWaitRender,
} from "../../services/api";

import type {
    Tile,
} from "../../services/api";

import {
    useRenderStore,
} from "../../store/renderStore";

const API = "http://127.0.0.1:8000";

export default function TileGrid({ onSelectTile }: { onSelectTile?: () => void }) {

    const [tiles, setTiles] = useState<Tile[]>([]);
    const [loading, setLoading] = useState(true);

    // Store

    const selectedTile = useRenderStore((s) => s.tile);

    const search = useRenderStore((s) => s.search);

    const category = useRenderStore((s) => s.category);

    const finish = useRenderStore((s) => s.finish);

    const tileSize = useRenderStore((s) => s.tileSize);

    const groutWidth = useRenderStore((s) => s.groutWidth);

    const groutColor = useRenderStore((s) => s.groutColor);

    const pattern = useRenderStore((s) => s.pattern);

    const setTile = useRenderStore((s) => s.setTile);

    const setImage = useRenderStore((s) => s.setImage);
    const setLoadingState = useRenderStore((s) => s.setLoading);

    const setProgress = useRenderStore((s) => s.setProgress);

    const setProgressMessage = useRenderStore((s) => s.setProgressMessage);

    // Load catalogue

    useEffect(() => {

        loadTiles();

    }, []);

    async function loadTiles() {

        try {

            const data = await getTiles();

            setTiles(data);

        }

        catch (err) {

            console.error(err);

        }

        finally {

            setLoading(false);

        }

    }

    // Render

    const renderTile = useCallback(async (tile: Tile) => {

        try {

            setLoadingState(true);

            setProgress(0);

            const response = await submitAndWaitRender({

                room: useRenderStore.getState().room,

                tile: tile.id,

                tile_size: tileSize,

                grout_width: groutWidth,

                grout_color: groutColor,

                pattern,

            }, (j) => {

                setProgress(j.progress ?? 0);

                setProgressMessage(j.message || j.status);

            });

            if (response.status === "done" && response.image) {

                setImage(

                    response.image +

                    "?t=" +

                    Date.now()

                );

            }

        }

        catch (err) {

            console.error(err);

        }

        finally {

            setLoadingState(false);

        }

    }, [

        tileSize,

        groutWidth,

        groutColor,

        pattern,

        setLoadingState,

        setImage,

        setProgress,

        setProgressMessage,

    ]);

    // Auto render whenever settings change

    useEffect(() => {

        if (tiles.length === 0)

            return;

        const tile = tiles.find(

            t => t.id === selectedTile

        );

        if (!tile)

            return;

        void renderTile(tile);

    }, [

        tileSize,

        groutWidth,

        groutColor,

        pattern,

        selectedTile,

        tiles,

        renderTile,

    ]);
    // Search + Filters

    const filteredTiles = useMemo(() => {

        return tiles.filter(tile => {

            const matchesSearch =

                search === "" ||

                tile.name.toLowerCase().includes(search.toLowerCase());

            const matchesCategory =

                category === "" ||

                tile.category === category;

            const matchesFinish =

                finish === "" ||

                tile.finish === finish;

            return (

                matchesSearch &&

                matchesCategory &&

                matchesFinish

            );

        });

    }, [

        tiles,

        search,

        category,

        finish,

    ]);

    // Click Tile

    function selectTile(tile: Tile) {

        setTile(tile.id);

       // renderTile(tile);

        onSelectTile?.();

    }

    if (loading)

        return (

            <Box

                sx={{

                    display: "flex",

                    justifyContent: "center",

                    alignItems: "center",

                    height: "100%",

                }}

            >

                <CircularProgress/>

            </Box>

        );

    return (

        <Box

            sx={{

                display: "flex",

                gap: 2,

                overflowX: "auto",

                px: 2,

                pb: 2,

            }}

        >

            {

                filteredTiles.map(tile => (

                    <Card

                        key={tile.id}

                        elevation={

                            selectedTile === tile.id

                                ? 10

                                : 2

                        }

                        sx={{

                            minWidth: 180,

                            flexShrink: 0,

                            cursor: "pointer",

                            border:

                                selectedTile === tile.id

                                    ? "3px solid #1976d2"

                                    : "1px solid #ddd",

                            borderRadius: 3,

                            transition: ".25s",

                            "&:hover": {

                                transform: "translateY(-5px)",

                            },

                        }}

                    >

                        <CardActionArea

                            onClick={() =>

                                selectTile(tile)

                            }

                        >

                            <CardMedia

                                component="img"

                                height="140"

                                image={`${API}${tile.thumbnail}`}

                                alt={tile.name}

                                sx={{

                                    objectFit: "cover",

                                }}

                                onError={(e) => {

                                    (

                                        e.target as HTMLImageElement

                                    ).src =

                                        "https://placehold.co/180x140?text=Tile";

                                }}

                            />

                            <CardContent>

                                <Typography

                                    sx={{ fontWeight: 700 }}

                                    noWrap

                                >

                                    {tile.name}

                                </Typography>

                                <Typography

                                    variant="body2"

                                    color="text.secondary"

                                >

                                    {tile.category}

                                </Typography>

                                <Typography

                                    variant="body2"

                                    color="text.secondary"

                                >

                                    {tile.finish}

                                </Typography>

                                <Typography

                                    variant="body2"

                                    color="text.secondary"

                                >

                                    {tile.size}

                                </Typography>

                            </CardContent>

                        </CardActionArea>

                    </Card>

                ))

            }

            {

                filteredTiles.length === 0 && (

                    <Box

                        sx={{

                            width: "100%",

                            textAlign: "center",

                            mt: 4,

                        }}

                    >

                        <Typography>

                            No tiles found.

                        </Typography>

                    </Box>

                )

            }

        </Box>

    );

}