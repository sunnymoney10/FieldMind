"""Bounded local Crawl4AI adapter; URLs supplied only by public discovery in this proof."""
from pathlib import Path
import sys,asyncio
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'proof'))
import retrieve

def fetch(output,targets,filename):
 retrieve.R=output;retrieve.TARGETS=targets;retrieve.OUTPUT_NAME=filename
 asyncio.run(retrieve.run())
