// script.js
// Otimizado para facilitar a interação básica do site

document.addEventListener("DOMContentLoaded", function () {
  // Realça o link ativo do menu conforme o scroll
  const navLinks = document.querySelectorAll("nav a");
  const sections = document.querySelectorAll("section");

  function onScroll() {
    let scrollPosition = document.documentElement.scrollTop || document.body.scrollTop;
    sections.forEach((section, idx) => {
      if (
        section.offsetTop <= scrollPosition + 80 &&
        section.offsetTop + section.offsetHeight > scrollPosition + 80
      ) {
        navLinks.forEach((link) => link.classList.remove("active"));
        navLinks[idx].classList.add("active");
      }
    });
  }

  window.addEventListener("scroll", onScroll);

  // Suave rolagem ao clicar nos links do menu
  navLinks.forEach(link => {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const targetId = this.getAttribute("href").slice(1);
      const section = document.getElementById(targetId);
      if (section) {
        window.scroll({
          top: section.offsetTop - 60,
          behavior: "smooth"
        });
      }
    });
  });

  // Exemplo de preenchimento dinâmico do email
  const contatoSection = document.querySelector("#contato p:last-child");
  if (contatoSection) {
    contatoSection.innerHTML = 'Email: <a href="mailto:leandro3810@email.com">leandro3810@email.com</a>';
  }
});
