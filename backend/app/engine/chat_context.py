"""Conversation-aware execution context for multi-turn chatflows.

``ChatExecutionContext`` extends the base ``ExecutionContext`` with:
- Loading persisted conversation variables on init so previous-turn outputs
  are available for variable resolution (``{{ n1.field }}``).
- Exposing ``chat.history`` (list of message dicts) to the execution
  environment so that nodes (e.g. LLM nodes) can access conversation
  context.

Usage::

    context = ChatExecutionContext(
        inputs={"message": user_text, ...},
        db=db_session,
        tenant_id=tenant_id,
        conversation=conv_obj,       # Conversation ORM instance
        history=message_dicts,       # list of {"role": ..., "content": ...}
    )
    executor.execute(inputs, context=context)

After execution the caller retrieves persistable outputs via
``context.get_persistable_outputs()`` and writes them back to the
conversation record.
"""

from app.engine.context import ExecutionContext


class ChatExecutionContext(ExecutionContext):
    """Conversation-aware execution context that persists variables across turns.

    Parameters
    ----------
    inputs : dict
        Input variables for the current turn, including ``message``.
    db : optional
        Database session.
    tenant_id : optional
        Current tenant identifier.
    conversation : Conversation, optional
        The ORM Conversation object whose ``variables`` field is loaded
        into the output context so that previous-turn results are resolved.
    history : list[dict], optional
        Conversation history list.  Each entry has ``role`` and ``content``.
    """

    def __init__(
        self,
        inputs: dict,
        db=None,
        tenant_id=None,
        conversation=None,
        history=None,
    ):
        super().__init__(inputs, db=db, tenant_id=tenant_id)
        self._conversation = conversation
        self._history = history or []

        # Load persisted variables from the conversation so that
        # node outputs from previous turns are visible via {{ n1.field }}.
        if conversation is not None and conversation.variables:
            self._outputs.update(conversation.variables)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def history(self) -> list[dict]:
        """Return the conversation history as a list of message dicts."""
        return list(self._history)

    def get_persistable_outputs(self) -> dict:
        """Return node outputs that should be saved to the conversation.

        The caller (the chat API endpoint) writes these back into
        ``conversation.variables`` so they survive across turns.
        """
        return dict(self._outputs)
