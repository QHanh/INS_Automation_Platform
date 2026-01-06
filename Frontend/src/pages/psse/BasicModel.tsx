import { useEffect } from "react";

export default function BasicModel() {
    useEffect(() => {
        document.title = 'Basic Model';
    }, []);

    return (
        <div>
            <h1>Basic Model</h1>
        </div>
    );
}
