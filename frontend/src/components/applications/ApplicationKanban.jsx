import React, { useState } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

const ApplicationKanban = () => {
  const [columns, setColumns] = useState({
    'applied': {
      id: 'applied',
      title: 'Applied',
      items: [
        { id: '1', company: 'Stripe', position: 'Senior React Engineer', date: '2024-01-15' },
        { id: '2', company: 'Vercel', position: 'DX Engineer', date: '2024-01-14' },
      ]
    },
    'reviewing': {
      id: 'reviewing',
      title: 'Reviewing',
      items: [
        { id: '3', company: 'Google', position: 'Frontend Developer', date: '2024-01-13' },
      ]
    },
    'interviewing': {
      id: 'interviewing',
      title: 'Interviewing',
      items: [
        { id: '4', company: 'Meta', position: 'UI Engineer', date: '2024-01-12' },
      ]
    },
    'offered': {
      id: 'offered',
      title: 'Offered',
      items: [
        { id: '5', company: 'Amazon', position: 'Frontend Lead', date: '2024-01-10' },
      ]
    },
    'rejected': {
      id: 'rejected',
      title: 'Rejected',
      items: []
    }
  });

  const onDragEnd = (result) => {
    const { destination, source, draggableId } = result;

    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;

    const sourceColumn = columns[source.droppableId];
    const destColumn = columns[destination.droppableId];
    const draggedItem = sourceColumn.items.find(item => item.id === draggableId);

    if (sourceColumn === destColumn) {
      const newItems = Array.from(sourceColumn.items);
      newItems.splice(source.index, 1);
      newItems.splice(destination.index, 0, draggedItem);
      
      setColumns({
        ...columns,
        [source.droppableId]: {
          ...sourceColumn,
          items: newItems
        }
      });
    } else {
      const sourceItems = Array.from(sourceColumn.items);
      sourceItems.splice(source.index, 1);
      
      const destItems = Array.from(destColumn.items);
      destItems.splice(destination.index, 0, draggedItem);
      
      setColumns({
        ...columns,
        [source.droppableId]: {
          ...sourceColumn,
          items: sourceItems
        },
        [destination.droppableId]: {
          ...destColumn,
          items: destItems
        }
      });
    }
  };

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {Object.values(columns).map((column) => (
          <div key={column.id} className="bg-gray-900  overflow-clip  p-4 mb-4">
            <div className="flex justify-between items-center mb-4 border-gray-200 border-b pb-2">
              <h3 className="font-semibold text-[15px] text-white">{column.title}</h3>
              <span className="bg-gray-800 px-2 py-1 rounded-full text-xs text-white">
                {column.items.length}
              </span>
            </div>
            <Droppable droppableId={column.id}>
              {(provided, snapshot) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className={` rounded-lg' ${
                    snapshot.isDraggingOver ? ' rounded-lg' : ''
                  }`}
                >
                  {column.items.map((item, index) => (
                    <Draggable key={item.id} draggableId={item.id} index={index}>
                      {(provided, snapshot) => ( 
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          className={` p-4 border bg-gray-800 border-gray-600 mb-3 rounded-lg shadow-sm ${
                            snapshot.isDragging ? 'shadow-lg' : ''
                          } `}
                        >
                          <h4 className="text-[17px] text-white">{item.position}</h4>
                          <p className="text-sm text-white">{item.company}</p>
                          <p className="text-xs text-white mt-2">{item.date}</p>
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </div>
        ))}
      </div>
    </DragDropContext>
  );
};

export default ApplicationKanban;