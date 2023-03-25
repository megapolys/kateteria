function activeLinkControl() {
    $('.navbar-nav .nav-link a').click(function () {
        $('.nav-link').removeClass('active')
        $(this).closest('.nav-link').addClass('active')
    })
}