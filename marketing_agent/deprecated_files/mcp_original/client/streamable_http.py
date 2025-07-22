import aiohttp
from contextlib import asynccontextmanager
from typing import AsyncIterator, Tuple, Optional
from aiohttp import ClientSession, ClientResponse

@asynccontextmanager
async def streamablehttp_client(url: str) -> AsyncIterator[Tuple[AsyncIterator[bytes], AsyncIterator[bytes], Optional[ClientResponse]]]:
    """HTTP client that supports streaming both request and response bodies.
    
    Args:
        url: The URL to connect to
        
    Returns:
        Tuple of (read_stream, write_stream, response)
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(url, chunked=True) as response:
            read_stream = response.content
            write_stream = response.content
            try:
                yield read_stream, write_stream, response
            finally:
                if not response.closed:
                    await response.release()