"""Excalidraw Real-time Collaboration Service.

Gerencia salas colaborativas para edição simultânea de diagramas.
"""

import json
import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect


class ExcalidrawCollaborationService:
    """Serviço de colaboração em tempo real para Excalidraw."""

    def __init__(self):
        """Inicializa o serviço de colaboração."""
        # Salas ativas: room_id -> set de WebSockets
        self._rooms: Dict[str, Set[WebSocket]] = {}
        
        # Metadados das salas: room_id -> metadata
        self._room_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Usuários por sala: room_id -> {user_id: user_info}
        self._room_users: Dict[str, Dict[str, Dict[str, Any]]] = {}

    async def join_room(
        self,
        room_id: str,
        websocket: WebSocket,
        user_id: str,
        user_name: str,
        patient_id: Optional[str] = None,
    ) -> None:
        """Adiciona um usuário a uma sala colaborativa.
        
        Args:
            room_id: ID da sala
            websocket: WebSocket do usuário
            user_id: ID do usuário
            user_name: Nome do usuário
            patient_id: ID do paciente (opcional)
        """
        # Criar sala se não existir
        if room_id not in self._rooms:
            self._rooms[room_id] = set()
            self._room_metadata[room_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "patient_id": patient_id,
            }
            self._room_users[room_id] = {}

        # Adicionar WebSocket à sala
        self._rooms[room_id].add(websocket)
        
        # Adicionar usuário
        self._room_users[room_id][user_id] = {
            "user_id": user_id,
            "user_name": user_name,
            "joined_at": datetime.utcnow().isoformat(),
        }

        # Notificar outros usuários
        await self._broadcast_to_room(
            room_id,
            {
                "type": "user-joined",
                "user_id": user_id,
                "user_name": user_name,
                "timestamp": datetime.utcnow().isoformat(),
            },
            exclude=websocket,
        )

        # Enviar lista de usuários para o novo usuário
        await websocket.send_json({
            "type": "room-state",
            "users": list(self._room_users[room_id].values()),
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def leave_room(
        self,
        room_id: str,
        websocket: WebSocket,
        user_id: str,
    ) -> None:
        """Remove um usuário de uma sala colaborativa.
        
        Args:
            room_id: ID da sala
            websocket: WebSocket do usuário
            user_id: ID do usuário
        """
        if room_id not in self._rooms:
            return

        # Remover WebSocket
        self._rooms[room_id].discard(websocket)
        
        # Remover usuário
        if user_id in self._room_users.get(room_id, {}):
            del self._room_users[room_id][user_id]

        # Notificar outros usuários
        await self._broadcast_to_room(
            room_id,
            {
                "type": "user-left",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Limpar sala se vazia
        if not self._rooms[room_id]:
            del self._rooms[room_id]
            del self._room_metadata[room_id]
            del self._room_users[room_id]

    async def broadcast_update(
        self,
        room_id: str,
        sender_ws: WebSocket,
        update_data: Dict[str, Any],
    ) -> None:
        """Broadcast de atualização de diagrama para todos na sala.
        
        Args:
            room_id: ID da sala
            sender_ws: WebSocket do remetente
            update_data: Dados da atualização (elements, appState, etc.)
        """
        if room_id not in self._rooms:
            return

        message = {
            "type": "diagram-update",
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self._broadcast_to_room(room_id, message, exclude=sender_ws)

    async def broadcast_cursor(
        self,
        room_id: str,
        sender_ws: WebSocket,
        user_id: str,
        cursor_data: Dict[str, Any],
    ) -> None:
        """Broadcast de posição do cursor para todos na sala.
        
        Args:
            room_id: ID da sala
            sender_ws: WebSocket do remetente
            user_id: ID do usuário
            cursor_data: Dados do cursor (x, y, etc.)
        """
        if room_id not in self._rooms:
            return

        message = {
            "type": "cursor-update",
            "user_id": user_id,
            "cursor": cursor_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self._broadcast_to_room(room_id, message, exclude=sender_ws)

    async def _broadcast_to_room(
        self,
        room_id: str,
        message: Dict[str, Any],
        exclude: Optional[WebSocket] = None,
    ) -> None:
        """Envia mensagem para todos os usuários de uma sala.
        
        Args:
            room_id: ID da sala
            message: Mensagem a enviar
            exclude: WebSocket a excluir (opcional)
        """
        if room_id not in self._rooms:
            return

        # Lista de WebSockets a remover (desconectados)
        to_remove = []

        for ws in self._rooms[room_id]:
            if ws == exclude:
                continue

            try:
                await ws.send_json(message)
            except Exception:
                # WebSocket desconectado
                to_remove.append(ws)

        # Remover WebSockets desconectados
        for ws in to_remove:
            self._rooms[room_id].discard(ws)

