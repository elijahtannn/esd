<template>
    <!-- Toasts -->
    <div class="toast-container position-fixed bottom-0 end-0 p-3">

        <!-- Toast if user is not logged in and want to buy tickets -->
        <div id="loginFirst" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-box-arrow-in-right text-black me-2"></i>
                <strong class="me-auto">Want to order tickets?</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                Log in now to buy tickets!
                <a href='/login'>Login here</a>
            </div>
        </div>

        <!-- Toast if user is not logged in and want to be notified of events -->
        <div id="loginFirstNotify" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-box-arrow-in-right text-black me-2"></i>
                <strong class="me-auto">Want to be notified?</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                Log in now to be notified of your interested events!
                <a href='/login'>Login here</a>
            </div>
        </div>

        <!-- Toast if user ran out of time while purchasing tickets -->
        <div id="timeOut" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-alarm-fill text-danger me-2"></i>
                <strong class="me-auto">Oops!</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                You ran out of time while buying tickets, please purchase again. 
            </div>
        </div>

        <!-- Toast if user payment declined -->
        <div id="paymentDecline" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-stripe text-danger me-2"></i>
                <strong class="me-auto">Oops!</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                Payment declined. Please try again.
            </div>
        </div>

        <!-- Toast if incomplete fields -->
        <div id="incompleteFields" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-input-cursor-text text-danger me-2"></i>
                <strong class="me-auto">Oops!</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                Please ensure that every fields are filled.
            </div>
        </div>

        <!-- Toast if there are insufficient tickets -->
        <div id="insufficientTickets" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-ticket-perforated-fill text-danger me-2"></i>
                <strong class="me-auto">Oops!</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                There is insufficient tickets for the selected category type
            </div>
        </div>


        <!-- PROFILE TOASTS -->

        <!-- Toast if mobile number has been updated -->
        <div id="updateMobile" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-telephone-fill text-success me-2"></i>
                <strong class="me-auto">Success!</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                Mobile number updated successfully!
            </div>
        </div>

        <!-- Toast if order is done loading -->
        <div id="orderLoadDone" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-ticket-perforated-fill text-success me-2"></i>
                <strong class="me-auto">Thanks for waiting!</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                Your order has successfully finish loading!
            </div>
        </div>

        <!-- Toast if listed ticket for resale -->
        <div id="resaleTicket" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-ticket-perforated-fill text-success me-2"></i>
                <strong class="me-auto">Success!</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                We have listed your ticket for resale on the market. Keep a look out in your email to be updated once your ticket has been sold.
            </div>
        </div>

        <!-- Toast if listed ticket for resale: error -->
        <div id="resaleTicketError" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-ticket-perforated-fill text-danger me-2"></i>
                <strong class="me-auto">Resale failed.</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                Unable to list ticket for resale.
            </div>
        </div>

        <!-- Toast if sent ticket for transfer -->
        <div id="transferTicket" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-ticket-perforated-fill text-success me-2"></i>
                <strong class="me-auto">How generous of you!</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                We have sent an email to the recepient of this ticket to accept the transfer. Do notify them to accept this as soon as possible. 
            </div>
        </div>

        <!-- Toast if sent ticket for transfer:error -->
        <div id="transferTicketError" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-ticket-perforated-fill text-danger me-2"></i>
                <strong class="me-auto">Transfer failed.</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                Unable to transfer ticket to recepient.
            </div>
        </div>

        <!-- Toast if user did not agree with terms and conditions -->
        <div id="agreeWithTnc" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-envelope-exclamation-fill text-danger me-2"></i>
                <strong class="me-auto">Terms and Conditions</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                You have to agree with the terms and conditions first.
            </div>
        </div>
        

        <!-- INTERESTED IN EVENTS -->

        <!-- Toast if user successfully registered for their interest in an event -->
        <div id="interestSuccess" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-envelope-exclamation-fill text-success me-2"></i>
                <strong class="me-auto">Successfully registered!</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                We'll notify you when this event tickets become available!
            </div>
        </div>

        <!-- Toast if user failed to registered for their interest in an event -->
        <div id="interestFailed" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-envelope-exclamation-fill text-danger me-2"></i>
                <strong class="me-auto">Failed to register.</strong>
                <span data-bs-dismiss="toast" aria-label="Close"><i class="bi bi-x-lg toastClose"></i></span>
            </div>
            <div class="toast-body">
                Failed to register for event tickets notification. Please try again.
            </div>
        </div>

        
        


    </div>
</template>