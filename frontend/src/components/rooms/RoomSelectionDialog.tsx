import { useEffect, useState } from "react";

import {
    Box,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    LinearProgress,
    Paper,
    Typography,
} from "@mui/material";

import {
    getRooms,
    submitAndWaitRender,
} from "../../services/api";

import type {
    Room,
} from "../../services/api";

import { useRenderStore } from "../../store/renderStore";

import { API } from "../../config";

export default function RoomSelectionDialog() {

    const [rooms, setRooms] = useState<Room[]>([]);

    const open = useRenderStore((s) => s.roomDialogOpen);

    const setOpen = useRenderStore((s) => s.setRoomDialogOpen);

    const tile = useRenderStore((s) => s.tile);

    const tileSize = useRenderStore((s) => s.tileSize);

    const groutWidth = useRenderStore((s) => s.groutWidth);

    const groutColor = useRenderStore((s) => s.groutColor);

    const pattern = useRenderStore((s) => s.pattern);

    const setRoom = useRenderStore((s) => s.setRoom);

    const setRoomName = useRenderStore((s) => s.setRoomName);

    const setImage = useRenderStore((s) => s.setImage);

    const setLoading = useRenderStore((s) => s.setLoading);

    const loading = useRenderStore((s) => s.loading);

    const progress = useRenderStore((s) => s.progress);

    const progressMessage = useRenderStore((s) => s.progressMessage);

    const setProgress = useRenderStore((s) => s.setProgress);

    const setProgressMessage = useRenderStore((s) => s.setProgressMessage);

    useEffect(() => {
        if (open) loadRooms();
    }, [open]);

    async function loadRooms() {

        try {

            const data = await getRooms();

            setRooms(data);

        }

        catch (err) {

            console.error(err);

        }

    }

    async function chooseRoom(room: Room) {

        // A Heavy AI job is CPU-intensive; never enqueue a second room render
        // while the current one is still running.
        if (loading) return;

        try {

            setLoading(true);

            setProgress(0);

            setProgressMessage("Submitting render...");

            setRoom(room.id);

            setRoomName(room.name);

            const job = await submitAndWaitRender({

                room: room.id,

                tile,

                tile_size: tileSize,

                grout_width: groutWidth,

                grout_color: groutColor,

                pattern,

            }, (j) => {

                setProgress(j.progress ?? 0);

                setProgressMessage(j.message || j.status);

            });

            if (job.status === "done" && job.image) {

                setImage(

                    job.image +

                    "?t=" +

                    Date.now()

                );

                setOpen(false);

            }

            else {

                console.error("Render failed:", job.message);

            }

        }

        catch (err) {

            console.error(err);

        }

        finally {

            setLoading(false);

        }

    }

    return (

        <Dialog

            open={open}

            onClose={() => setOpen(false)}

            maxWidth="md"

            fullWidth

        >

            <DialogTitle>

                Select Room

            </DialogTitle>

            <DialogContent>

                <Box

                    sx={{

                        display: "grid",

                        gridTemplateColumns: "repeat(auto-fill,minmax(220px,1fr))",

                        gap: 2,

                        mt: 1,

                    }}

                >

                    {rooms.map((room) => (

                        <Paper

                            key={room.id}

                            elevation={4}

                            onClick={() => chooseRoom(room)}

                            sx={{

                                cursor: loading ? "wait" : "pointer",

                                pointerEvents: loading ? "none" : "auto",

                                borderRadius: 3,

                                overflow: "hidden",

                                transition: ".25s",

                                "&:hover": {

                                    transform: loading ? "none" : "translateY(-5px)",

                                    boxShadow: 8,

                                },

                            }}

                        >

                            <Box

                                component="img"

                                src={`${API}${room.thumbnail ?? room.image}`}

                                alt={room.name}

                                sx={{

                                    width: "100%",

                                    height: 150,

                                    objectFit: "cover",

                                }}

                            />

                            <Box sx={{ p: 2 }}>

                                <Typography

                                    sx={{ fontWeight: 700, textAlign: "center" }}

                                >

                                    {room.name}

                                </Typography>

                            </Box>

                        </Paper>

                    ))}

                </Box>

            </DialogContent>

            <DialogActions>

                <Button

                    onClick={() => setOpen(false)}

                    disabled={loading}

                >

                    Cancel

                </Button>

            </DialogActions>

            {loading && (

                <Box sx={{ px: 3, pb: 2 }}>

                    <LinearProgress

                        variant="determinate"

                        value={Math.round(progress * 100)}

                    />

                    <Typography

                        variant="caption"

                        sx={{ display: "block", mt: 1, textAlign: "center" }}

                    >

                        {progressMessage || "Rendering..."} ({Math.round(progress * 100)}%)

                    </Typography>

                </Box>

            )}

        </Dialog>

    );

}