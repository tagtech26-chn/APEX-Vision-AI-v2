import { Box, CircularProgress, Fade, LinearProgress, Typography } from "@mui/material";
import { useRenderStore } from "../../store/renderStore";

const API = "http://127.0.0.1:8000";

export default function PreviewCanvas() {

    const image = useRenderStore((s) => s.image);
    const loading = useRenderStore((s) => s.loading);
    const progress = useRenderStore((s) => s.progress);
    const progressMessage = useRenderStore((s) => s.progressMessage);
    const roomName = useRenderStore((s) => s.roomName);

    return (

        <Box

            sx={{

                position: "absolute",

                top: 0,

                left: 0,

                right: 0,

                bottom: 0,

                overflow: "hidden",

                bgcolor: "#000",

            }}

        >

            {

                loading &&

                <Box

                    sx={{

                        position: "absolute",

                        inset: 0,

                        display: "flex",

                        flexDirection: "column",

                        justifyContent: "center",

                        alignItems: "center",

                        gap: 2,

                        zIndex: 100,

                        bgcolor: "rgba(0,0,0,.35)",

                        backdropFilter: "blur(4px)",

                    }}

                >

                    <CircularProgress

                        color="inherit"

                        size={60}

                    />

                    <Box

                        sx={{

                            width: "min(320px, 60vw)",

                        }}

                    >

                        <LinearProgress

                            color="inherit"

                            variant="determinate"

                            value={Math.round(progress * 100)}

                        />

                        <Typography

                            color="white"

                            variant="caption"

                            sx={{ display: "block", mt: 1, textAlign: "center" }}

                        >

                            {progressMessage || "Rendering..."} ({Math.round(progress * 100)}%)

                        </Typography>

                    </Box>

                </Box>

            }

            <Fade

                in

                timeout={300}

            >

                <Box

                    component="img"

                    src={image.startsWith("http") ? image : `${API}${image}`}

                    sx={{

                        width: "100%",

                        height: "100%",

                        objectFit: "contain",

                        objectPosition: "center",

                        transition: ".35s",

                        userSelect: "none",

                        pointerEvents: "none",

                    }}

                />

            </Fade>

                <Typography

                    sx={{

                        position: "absolute",

                        left: 16,

                        bottom: 14,

                        color: "rgba(255,255,255,.9)",

                        fontWeight: 700,

                        fontSize: 18,

                        textShadow: "0 1px 4px rgba(0,0,0,.7)",

                        pointerEvents: "none",

                        zIndex: 50,

                    }}

                >

                    {roomName}

                </Typography>

        </Box>

    );

}