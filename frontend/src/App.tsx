import Header from "./components/layout/Header";
import PreviewCanvas from "./components/layout/PreviewCanvas";
import FloatingPanel from "./components/floating/FloatingPanel";
import BottomGallery from "./components/gallery/BottomGallery";
import FloatingToolbar from "./components/layout/FloatingToolbar";
import RoomSelectionDialog from "./components/rooms/RoomSelectionDialog";

export default function App() {

    return (
        <>
            <Header />

            <PreviewCanvas />

            <FloatingPanel />

            <FloatingToolbar />

            <BottomGallery />

            <RoomSelectionDialog />
        </>
    );

}