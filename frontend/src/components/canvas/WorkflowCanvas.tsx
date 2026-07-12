import React, { useCallback, useRef, useState, DragEvent } from 'react';
import ReactFlow, { useReactFlow, Background, Controls, Node, NodeTypes } from 'reactflow';
import 'reactflow/dist/style.css';
import { useWorkflowStore } from '../../stores/workflowStore';

interface WorkflowCanvasProps {
  nodeTypes?: NodeTypes;
}

interface ContextMenuState {
  visible: boolean;
  x: number;
  y: number;
  node: Node | null;
}

const WorkflowCanvas: React.FC<WorkflowCanvasProps> = ({ nodeTypes }) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const reactFlowInstance = useReactFlow();
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, addNode, selectNode } =
    useWorkflowStore();

  const [menu, setMenu] = useState<ContextMenuState>({ visible: false, x: 0, y: 0, node: null });

  const closeMenu = useCallback(() => setMenu(s => ({ ...s, visible: false })), []);

  const onDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: DragEvent) => {
      event.preventDefault();
      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;
      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });
      addNode(type, position);
    },
    [reactFlowInstance, addNode]
  );

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      selectNode(node);
    },
    [selectNode]
  );

  const onPaneClick = useCallback(() => {
    selectNode(null);
    closeMenu();
  }, [selectNode, closeMenu]);

  // --- Right-click context menu ---
  const onNodeContextMenu = useCallback(
    (event: React.MouseEvent, node: Node) => {
      event.preventDefault();
      selectNode(node);
      setMenu({ visible: true, x: event.clientX - 250, y: event.clientY - 80, node });
    },
    [selectNode]
  );

  const onPaneContextMenu = useCallback(
    (event: React.MouseEvent | any) => {
      event.preventDefault?.();
      closeMenu();
    },
    [closeMenu]
  );

  const handleDeleteNode = useCallback(() => {
    if (!menu.node) return;
    onNodesChange([{ type: 'remove', id: menu.node.id }]);
    closeMenu();
  }, [menu.node, onNodesChange, closeMenu]);

  const handleDuplicateNode = useCallback(() => {
    if (!menu.node) return;
    const pos = { x: (menu.node.position?.x || 0) + 80, y: (menu.node.position?.y || 0) + 80 };
    addNode(menu.node.type || 'input', pos);
    closeMenu();
  }, [menu.node, addNode, closeMenu]);

  return (
    <div ref={reactFlowWrapper} style={{ width: '100%', height: '100%', position: 'relative' }} onClick={closeMenu}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        onNodeContextMenu={onNodeContextMenu}
        onPaneContextMenu={onPaneContextMenu}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>

      {/* Context Menu */}
      {menu.visible && (
        <div
          style={{
            position: 'absolute',
            top: menu.y,
            left: menu.x,
            background: '#fff',
            border: '1px solid #e8e8e8',
            borderRadius: 6,
            boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
            padding: '4px 0',
            minWidth: 150,
            zIndex: 1000,
            fontSize: 13,
          }}
        >
          {menu.node ? (
            <>
              <MenuItem onClick={handleDuplicateNode}>🔁 复制节点</MenuItem>
              <MenuItem onClick={() => { selectNode(menu.node); closeMenu(); }}>⚙️ 配置</MenuItem>
              <div style={{ height: 1, background: '#f0f0f0', margin: '4px 0' }} />
              <MenuItem onClick={handleDeleteNode} danger>🗑️ 删除</MenuItem>
            </>
          ) : (
            <>
              <MenuItem onClick={() => addNode('input', reactFlowInstance.getViewport())}>➕ 输入节点</MenuItem>
              <MenuItem onClick={() => addNode('llm', reactFlowInstance.getViewport())}>➕ LLM 节点</MenuItem>
              <MenuItem onClick={() => addNode('output', reactFlowInstance.getViewport())}>➕ 输出节点</MenuItem>
            </>
          )}
        </div>
      )}
    </div>
  );
};

// Menu item helper
const MenuItem: React.FC<{ onClick: () => void; children: React.ReactNode; danger?: boolean }> = ({ onClick, children, danger }) => (
  <div
    onClick={onClick}
    style={{
      padding: '6px 16px',
      cursor: 'pointer',
      color: danger ? '#ff4d4f' : '#333',
      display: 'flex',
      alignItems: 'center',
      gap: 6,
    }}
    onMouseEnter={(e) => (e.currentTarget.style.background = '#f5f5f5')}
    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
  >
    {children}
  </div>
);

export default WorkflowCanvas;
