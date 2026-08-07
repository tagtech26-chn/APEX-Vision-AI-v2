import {
    Box,
    Fab,
    Tooltip,
} from "@mui/material";

import CameraAltIcon from "@mui/icons-material/CameraAlt";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import ZoomInIcon from "@mui/icons-material/ZoomIn";
import ZoomOutIcon from "@mui/icons-material/ZoomOut";
import HomeIcon from "@mui/icons-material/Home";

import { useRenderStore } from "../../store/renderStore";

export default function FloatingToolbar() {

    const setRoomDialogOpen = useRenderStore(
        (s) => s.setRoomDialogOpen
    );

    return (

        <Box

            sx={{

                position: "absolute",

                right: 25,

                top: 110,

                display: "flex",

                flexDirection: "column",

                gap: 2,

                zIndex: 120,

            }}

        >

            <Tooltip title="Change Room">

                <Fab

                    color="primary"

                    size="medium"

                    onClick={() =>

                        setRoomDialogOpen(true)

                    }

                >

                    <HomeIcon />

                </Fab>

            </Tooltip>

            <Tooltip title="Zoom In">

                <Fab

                    color="primary"

                    size="medium"

                >

                    <ZoomInIcon />

                </Fab>

            </Tooltip>

            <Tooltip title="Zoom Out">

                <Fab

                    color="primary"

                    size="medium"

                >

                    <ZoomOutIcon />

                </Fab>

            </Tooltip>

            <Tooltip title="Take Snapshot">

                <Fab

                    color="secondary"

                    size="medium"

                >

                    <CameraAltIcon />

                </Fab>

            </Tooltip>

            <Tooltip title="Reset View">

                <Fab

                    color="default"

                    size="medium"

                >

                    <RestartAltIcon />

                </Fab>

            </Tooltip>

            <Tooltip title="Fullscreen">

                <Fab

                    color="default"

                    size="medium"

                >

                    <FullscreenIcon />

                </Fab>

            </Tooltip>

        </Box>

    );

}