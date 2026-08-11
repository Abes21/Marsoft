/* Motyw: jasny / ciemny / systemowy (RF-75, RF-76). */
(function () {
  var KEY = "theme";

  function apply() {
    var pref = localStorage.getItem(KEY) || "system";
    var dark =
      pref === "dark" ||
      (pref === "system" &&
        window.matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  }

  apply();

  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", apply);

  window.addEventListener("DOMContentLoaded", function () {
    var select = document.getElementById("theme-select");
    if (!select) return;

    select.value = localStorage.getItem(KEY) || "system";

    select.addEventListener("change", function () {
      localStorage.setItem(KEY, select.value);
      apply();
    });
  });
})();
