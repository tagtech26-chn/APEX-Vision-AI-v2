import {
    Card,
    CardActionArea,
    CardMedia,
    CardContent,
    Typography
} from "@mui/material";

import type { Room } from "../../services/api";

import { API } from "../../config";

interface Props{

    room:Room;

    selected:boolean;

    onClick:()=>void;

}

export default function RoomCard({

    room,

    selected,

    onClick,

}:Props){

    return(

        <Card

            elevation={selected?8:2}

            sx={{

                width:180,

                minWidth:180,

                borderRadius:3,

                border:selected?

                    "3px solid #1976d2"

                    :

                    "1px solid #ddd",

                transition:".25s",

                "&:hover":{

                    transform:"translateY(-4px)"

                }

            }}

        >

            <CardActionArea onClick={onClick}>

                <CardMedia

                    component="img"

                    height="110"

                    image={`${API}${room.thumbnail}`}

                />

                <CardContent>

                    <Typography

                        sx={{ fontWeight: 700 }}

                        noWrap

                    >

                        {room.name}

                    </Typography>

                </CardContent>

            </CardActionArea>

        </Card>

    );

}