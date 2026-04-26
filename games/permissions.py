from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsHostOrReadOnly(BasePermission):
    participant_actions = {'join', 'leave', 'confirm_attendance'}
    host_only_actions = {'approve_participant', 'reject_participant', 'mark_participant_status'}

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        action = getattr(view, 'action', None)
        if action in self.participant_actions:
            return True
        if action in self.host_only_actions:
            return obj.host_id == request.user.id
        return obj.host_id == request.user.id
