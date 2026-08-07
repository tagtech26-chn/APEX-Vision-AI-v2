import {

    Box,

    Typography,

} from "@mui/material";

import {

    useEffect,

    useState,

} from "react";

import {

    getRooms,

    submitAndWaitRender,

    type Room,

} from "../../services/api";

import {

    useRenderStore,

} from "../../store/renderStore";

import RoomCard from "./RoomCard";

export default function RoomGallery(){

    const [rooms,setRooms]=useState<Room[]>([]);

    const room=useRenderStore(s=>s.room);

    const tile=useRenderStore(s=>s.tile);

    const groutWidth=useRenderStore(s=>s.groutWidth);

    const groutColor=useRenderStore(s=>s.groutColor);

    const pattern=useRenderStore(s=>s.pattern);

    const setRoom=useRenderStore(s=>s.setRoom);

    const setImage=useRenderStore(s=>s.setImage);

    useEffect(()=>{

        load();

    },[]);

    async function load(){

        const data=await getRooms();

        setRooms(data);

    }

    async function changeRoom(id:number){

        setRoom(id);

        const result = await submitAndWaitRender({

            room: id,

            tile,

            tile_size: 600,

            grout_width: groutWidth,

            grout_color: groutColor,

            pattern,

        });

        if (result.status === "done" && result.image) {

            setImage(

                result.image +

                "?t=" + Date.now()

            );

        }

    }

    return(

        <Box sx={{ px: 2, py: 1 }}>

            <Typography

                variant="h6"

                sx={{ mb: 2, fontWeight: 700 }}

            >

                Rooms

            </Typography>

            <Box

                sx={{

                    display:"flex",

                    gap:2,

                    overflowX:"auto",

                }}

            >

                {

                    rooms.map(r=>(

                        <RoomCard

                            key={r.id}

                            room={r}

                            selected={room===r.id}

                            onClick={()=>changeRoom(r.id)}

                        />

                    ))

                }

            </Box>

        </Box>

    );

}