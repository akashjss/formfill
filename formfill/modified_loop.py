import logging
from typing import cast, Any

from anthropic import AsyncAnthropic
from anthropic.types.beta import BetaMessageParam, BetaToolResultBlockParam
from PIL import Image

from .anthropic_computer_use_demo.loop import COMPUTER_USE_BETA_FLAG, _response_to_params, _make_api_tool_result
from .anthropic_computer_use_demo.tools.collection import ToolCollection

from .pdf_editor import PDFEditorTool

logger = logging.getLogger("formfill")


async def sampling_loop(
    *,
    model: str,
    messages: list[BetaMessageParam],
    max_tokens: int = 4096,
    img: Image.Image,
):
    """
    Agentic sampling loop for the assistant/tool interaction of computer use.
    """
    pdf_editor =  PDFEditorTool(img)
    tool_collection = ToolCollection(
       pdf_editor,
    )

    while True:
        betas = [COMPUTER_USE_BETA_FLAG]
        client = AsyncAnthropic()
        
        response = await client.beta.messages.create(
            max_tokens=max_tokens,
            messages=messages,
            model=model,
            tools=tool_collection.to_params(),
            betas=betas,
        )
        logger.debug(response)
        
        response_params = _response_to_params(response)
        messages.append(
            {
                "role": "assistant",
                "content": response_params,
            }
        )

        tool_result_content: list[BetaToolResultBlockParam] = []
        for content_block in response_params:
            if content_block["type"] == "tool_use":
                result = await tool_collection.run(
                    name=content_block["name"],
                    tool_input=cast(dict[str, Any], content_block["input"]),
                )
                tool_result_content.append(
                    _make_api_tool_result(result, content_block["id"])
                )

        if not tool_result_content:
            return pdf_editor.get_edited_pdf()

        messages.append({"content": tool_result_content, "role": "user"})