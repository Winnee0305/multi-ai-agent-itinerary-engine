#!/usr/bin/env python3
"""
Generate and save visualizations of the LangGraph supervisor graph.

This script creates:
1. Mermaid diagram (text format)
2. PNG image (visual diagram using graphviz)
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from langchain_google_genai import ChatGoogleGenerativeAI
from agents.supervisor_graph import create_supervisor_graph
from config.settings import settings


def visualize_graph():
    """Generate and save graph visualizations."""
    
    print("=" * 80)
    print("LangGraph Supervisor Graph Visualization")
    print("=" * 80)
    
    # Initialize LLM model
    print("\n1. Initializing LLM model...")
    model = ChatGoogleGenerativeAI(
        model=settings.DEFAULT_LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE
    )
    print(f"   ✓ Using model: {settings.DEFAULT_LLM_MODEL}")
    
    # Create supervisor graph
    print("\n2. Creating supervisor graph...")
    compiled_graph = create_supervisor_graph(model)
    print("   ✓ Graph created and compiled successfully")
    
    # Get the graph object
    graph_obj = compiled_graph.get_graph()
    
    # 1. Mermaid Diagram
    print("\n3. Generating Mermaid diagram...")
    mermaid_diagram = None
    try:
        mermaid_diagram = graph_obj.draw_mermaid()
        
        # Save Mermaid to file
        mermaid_file = "langgraph_visualization.mmd"
        with open(mermaid_file, "w") as f:
            f.write(mermaid_diagram)
        print(f"   ✓ Mermaid diagram saved to: {mermaid_file}")
        
        # Also print it
        print("\n" + "=" * 80)
        print("MERMAID DIAGRAM (copy to https://mermaid.live/)")
        print("=" * 80)
        print(mermaid_diagram)
        print("=" * 80 + "\n")
    except Exception as e:
        print(f"   ✗ Mermaid generation failed: {e}")
    
    # 2. PNG Diagram using mermaid CLI
    print("4. Generating PNG diagram...")
    png_generated = False
    
    # Try using mmdc (mermaid-cli) if available
    try:
        import subprocess
        import json
        
        # Use mermaid-cli if installed
        result = subprocess.run(
            ["npx", "mermaid-cli", "-i", "langgraph_visualization.mmd", "-o", "langgraph_visualization.png"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            file_size = os.path.getsize("langgraph_visualization.png") / 1024
            print(f"   ✓ PNG saved to: langgraph_visualization.png ({file_size:.1f} KB)")
            png_generated = True
        else:
            raise Exception(f"mmdc failed: {result.stderr}")
    except Exception as e:
        print(f"   ⚠ Trying alternative PNG generation method...")
        
        # Try using dot command (from graphviz) to generate PNG from mermaid
        # First, convert mermaid to dot format using a simple Python script
        try:
            # Create a simple visualization using graphviz dot format
            dot_content = """digraph {
    rankdir=LR;
    node [shape=box, style=filled, fillcolor="#f2f0ff"];
    
    __start__ [shape=ellipse, fillcolor="transparent"];
    __end__ [shape=ellipse, fillcolor="#bfb6fc"];
    
    __start__ -> parse_input;
    parse_input -> recommend [style=dashed];
    parse_input -> __end__ [style=dashed];-
    recommend -> plan [style=dashed];
    recommend -> __end__ [style=dashed];
    plan -> format_response [style=dashed];
    plan -> __end__ [style=dashed];
    format_response -> __end__ [style=dashed];
}"""
            
            dot_file = "langgraph_visualization.dot"
            with open(dot_file, "w") as f:
                f.write(dot_content)
            
            # Use dot command to generate PNG
            result = subprocess.run(
                ["dot", "-Tpng", dot_file, "-o", "langgraph_visualization.png"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                file_size = os.path.getsize("langgraph_visualization.png") / 1024
                print(f"   ✓ PNG saved to: langgraph_visualization.png ({file_size:.1f} KB)")
                png_generated = True
            else:
                raise Exception(f"dot command failed: {result.stderr}")
        except Exception as e2:
            print(f"   ✗ PNG generation failed: {e2}")
            print("   Note: You can still view the diagram at: https://mermaid.live/")
    
    print("\n" + "=" * 80)
    print("Visualization Complete!")
    print("=" * 80)
    print("\nGenerated files:")
    print("  - langgraph_visualization.mmd  (Mermaid diagram - text)")
    if png_generated:
        print("  - langgraph_visualization.png  (PNG image)")
    else:
        print("  - langgraph_visualization.png  (PNG generation failed - see notes above)")
    print("\nTo view the Mermaid diagram online:")
    print("  1. Open https://mermaid.live/")
    print("  2. Copy contents of .mmd file")
    print("  3. Paste into the Mermaid editor")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    visualize_graph()
