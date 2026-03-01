from typing import Tuple
from typing import Union

from pydantic import BaseModel
from pydantic import Field


class Color(BaseModel):
    """Validated RGBA color (0–255 per channel)"""

    r: int = Field(..., ge=0, le=255)
    g: int = Field(..., ge=0, le=255)
    b: int = Field(..., ge=0, le=255)
    a: int = Field(255, ge=0, le=255)

    @classmethod
    def from_any(cls, value: Union[str, tuple, list]) -> "Color":
        if isinstance(value, str):
            hex_str = value.lstrip("#").lower()
            if len(hex_str) in (6, 8):
                return cls(
                    r=int(hex_str[0:2], 16),
                    g=int(hex_str[2:4], 16),
                    b=int(hex_str[4:6], 16),
                    a=int(hex_str[6:8], 16) if len(hex_str) == 8 else 255,
                )
            raise ValueError(f"Invalid hex string: {value!r}")

        if isinstance(value, (tuple, list)):
            nums = [int(x) for x in value]
            if len(nums) == 3:
                return cls(r=nums[0], g=nums[1], b=nums[2], a=255)
            if len(nums) == 4:
                return cls(r=nums[0], g=nums[1], b=nums[2], a=nums[3])
            raise ValueError(f"Expected 3 or 4 numbers, got {len(nums)}")

        raise ValueError(f"Cannot parse color from: {value!r}")

    def rgb_tuple(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def __str__(self) -> str:
        if self.a == 255:
            return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}{self.a:02x}"
