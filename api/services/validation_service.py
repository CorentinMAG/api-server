"""
Validation Service for transfer request business rules.

This service handles validation logic for transfer requests,
policies, and business constraints.
"""
from __future__ import annotations

from typing import List, Optional

from dtr_common.constantes import State as StateEnum

from api.models import TransferPolicy, TransferRequest
from api.repositories import TransferRequestRepository


class ValidationService:
    """Service for validating transfer request business rules."""

    def __init__(self, transfer_request_repo: TransferRequestRepository, logger=None):
        """
        Initialize validation service with dependencies.

        Args:
            transfer_request_repo: Repository for transfer request operations
            logger: Logger instance for validation operations
        """
        self.transfer_request_repo = transfer_request_repo
        self.logger = logger

    def can_purge_request(self, request: Optional[TransferRequest]) -> bool:
        """
        Check if a transfer request can be purged based on business rules.

        A request can be purged if all associated transfer requests
        (same filename and policy) have been completed successfully.

        Args:
            request: Transfer request to check for purging

        Returns:
            True if request can be purged, False otherwise
        """
        if request is None:
            return False

        # Find all associated transfer requests with same filename and policy
        associated_requests = self.transfer_request_repo.find_associated_requests(
            filename=request.filename, policy_id=request.policy_id, exclude_id=request.id
        )

        if self.logger:
            self.logger.debug(f"Found {len(associated_requests)} associated transfer requests")

        # Check if all associated requests have been completed successfully
        for tr in associated_requests:
            if not any(state.state == StateEnum.SUCCESSFUL for state in tr.states):
                if self.logger:
                    self.logger.debug(f"Transfer request {tr.id} not successful")
                return False

        if self.logger:
            self.logger.debug("Authorize worker to purge source")
        return True

    def validate_file_for_policy(self, filename: str, policy_id: int, only_new_data: bool) -> bool:
        """
        Validate if a file can be processed for a given policy.

        Args:
            filename: Name of the file to validate
            policy_id: Transfer policy ID
            only_new_data: Whether policy only accepts new data

        Returns:
            True if file can be processed, False otherwise
        """
        # Get existing filenames for this policy
        existing_filenames = self.transfer_request_repo.get_existing_filenames_for_policy(
            policy_id, {filename}
        )

        # If file doesn't exist, it can always be processed
        if filename not in existing_filenames:
            return True

        # If policy only accepts new data and file exists, reject
        if only_new_data:
            return False

        # For non-new-data policies, check if all previous requests are finished
        unfinished_count = self.transfer_request_repo.count_unfinished_requests_for_file(policy_id, filename)

        return unfinished_count == 0

    def filter_valid_files(
        self, filenames: List[str], policy_id: int, only_new_data: bool, max_files: int
    ) -> List[str]:
        """
        Filter list of files to only include those valid for processing.

        Args:
            filenames: List of filenames to filter
            policy_id: Transfer policy ID
            only_new_data: Whether policy only accepts new data
            max_files: Maximum number of files to return

        Returns:
            List of valid filenames (up to max_files)
        """
        valid_files = []

        # Get existing filenames in batch for efficiency
        filename_set = set(filenames)
        existing_filenames = self.transfer_request_repo.get_existing_filenames_for_policy(
            policy_id, filename_set
        )

        for filename in filenames:
            if len(valid_files) >= max_files:
                break

            # Check if file is new
            if filename not in existing_filenames:
                valid_files.append(filename)
                continue

            # Skip if policy only accepts new data
            if only_new_data:
                continue

            # Check if all previous requests for this file are finished
            unfinished_count = self.transfer_request_repo.count_unfinished_requests_for_file(
                policy_id, filename
            )

            if unfinished_count == 0:
                valid_files.append(filename)

        return valid_files

    def validate_policy_constraints(self, policy: TransferPolicy, num_files: int) -> tuple[bool, str]:
        """
        Validate constraints for a transfer policy.

        Args:
            policy: Transfer policy to validate
            num_files: Number of files to be processed

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not policy:
            return False, "Transfer policy not found"

        if not policy.enabled:
            return False, f"Transfer policy '{policy.name}' is disabled"

        if not policy.dests:
            return False, f"No destinations configured for policy '{policy.name}'"

        if num_files <= 0:
            return False, "No files to process"

        return True, ""

    def can_create_transfer_for_destination(
        self, policy_name: str, filename: str, dest_id: int
    ) -> tuple[bool, str]:
        """
        Check if a transfer can be created for a specific destination.

        Args:
            policy_name: Name of the transfer policy
            filename: File to transfer
            dest_id: Destination ID

        Returns:
            Tuple of (can_create, reason)
        """
        # Check for existing transfer in progress
        existing_request = self.transfer_request_repo.find_in_progress_for_destination(
            policy_name, filename, dest_id
        )

        if existing_request:
            return False, f"Transfer already in progress: {filename}"

        return True, ""
