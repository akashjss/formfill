import base64
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from PIL import Image

from .anthropic_computer_use_demo.tools.computer import ComputerTool, Action, ScalingSource, OUTPUT_DIR
from .anthropic_computer_use_demo.tools.base import ToolError, ToolResult

from .image_utils import overlay_cursor, add_text_to_image, resize_for_editing, restore_from_editing


class PDFEditorTool(ComputerTool):
    def __init__(self, img):
        super().__init__()

        self.current_position = (0,0)

        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        self.path = output_dir / f"screenshot_{uuid4().hex}.png"
        self.original_size = img.size
        resized = resize_for_editing(img, self.width, self.height)
        resized.save(self.path, "PNG")

    def get_edited_pdf(self):
        return restore_from_editing(Image.open(self.path), self.original_size)

    def validate_action(
        self,
        *,
        action: Action,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        super().validate_action(
            action=action,
            text=text,
            coordinate=coordinate,
            **kwargs
        )

        if action in [
            "left_click_drag",
            "key"
        ]:
            raise ToolError(f"{action} not supported")

    async def __call__(
        self,
        *,
        action: Action,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        self.validate_action(action=action, text=text, coordinate=coordinate, **kwargs)

        if action == "mouse_move":            
            x, y = self.scale_coordinates(
                ScalingSource.API, coordinate[0], coordinate[1]
            )
            return await self.mouse_move(x, y)

        if action == "type":
            return await self.type(text)

        if action in (
            "left_click",
            "right_click",
            "double_click",
            "middle_click",
            "screenshot",
            "cursor_position",
        ):
            if action == "screenshot":
                return await self.screenshot()
            elif action == "cursor_position":
                x, y = self.scale_coordinates(
                    ScalingSource.COMPUTER,
                    self.current_position[0],
                    self.current_position[1]
                )
                return ToolResult(output=f"X={x},Y={y}", error="")
            else:
                return ToolResult(output="Clicked", error="")

        raise ToolError(f"Invalid action: {action}")

    async def screenshot(self):
        """Take a screenshot of the current screen and return the base64 encoded image."""

        result = ToolResult(output="", error="", base64_image="")

        if self.path.exists():
            return result.replace(
                base64_image=base64.b64encode(self.path.read_bytes()).decode()
            )
        raise ToolError(f"Failed to take screenshot: {result.error}")

    async def type(self, text) -> ToolResult:
        x, y = self.scale_coordinates(
            ScalingSource.COMPUTER,
            self.current_position[0],
            self.current_position[1]
        )
        add_text_to_image(self.path, text, (x,y))
        return await self.screenshot()
    
    async def mouse_move(self, x, y) -> ToolResult:
        self.current_position = (x, y)
        
        img = overlay_cursor(self.path, (x, y))

        # Create a bytes buffer
        buffered = BytesIO()
        
        # Save the image as PNG to the buffer
        img.save(buffered, format="PNG")
        
        # Get the byte value from the buffer
        img_bytes = buffered.getvalue()
        
        # Encode to base64 and decode to string
        img_base64 = base64.b64encode(img_bytes).decode()

        return ToolResult(output="Moved mouse", error="", base64_image=img_base64)