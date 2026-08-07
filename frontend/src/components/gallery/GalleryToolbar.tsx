import {
    Box,
    IconButton,
    Tooltip,
    Typography,
} from "@mui/material";

import ViewModuleIcon from "@mui/icons-material/ViewModule";
import ViewListIcon from "@mui/icons-material/ViewList";
import FavoriteBorderIcon from "@mui/icons-material/FavoriteBorder";
import HistoryIcon from "@mui/icons-material/History";

export default function GalleryToolbar() {

    return (

        <Box

            sx={{

                display:"flex",

                justifyContent:"space-between",

                alignItems:"center",

                mb:2,

            }}

        >

            <Typography

                variant="h6"

                sx={{ fontWeight: 700 }}

            >

                Tile Catalogue

            </Typography>

            <Box>

                <Tooltip title="Grid View">

                    <IconButton>

                        <ViewModuleIcon/>

                    </IconButton>

                </Tooltip>

                <Tooltip title="List View">

                    <IconButton>

                        <ViewListIcon/>

                    </IconButton>

                </Tooltip>

                <Tooltip title="Favorites">

                    <IconButton>

                        <FavoriteBorderIcon/>

                    </IconButton>

                </Tooltip>

                <Tooltip title="Recent">

                    <IconButton>

                        <HistoryIcon/>

                    </IconButton>

                </Tooltip>

            </Box>

        </Box>

    );

}