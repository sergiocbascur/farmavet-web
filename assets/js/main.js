document.addEventListener("DOMContentLoaded", () => {
  const navToggle = document.querySelector("[data-nav-toggle]");
  const navLinks = document.querySelector("[data-nav-links]");
  const navLinkItems = document.querySelectorAll("[data-nav-link]");

  if (navToggle && navLinks) {
    // Toggle del botón hamburguesa
    navToggle.addEventListener("click", () => {
      const expanded = navToggle.getAttribute("aria-expanded") === "true";
      navToggle.setAttribute("aria-expanded", String(!expanded));
      navLinks.classList.toggle("open");
      document.body.classList.toggle("no-scroll", !expanded);
    });
    
    // Función para cerrar el menú
    const closeMenu = () => {
      navLinks.classList.remove("open");
      navToggle.setAttribute("aria-expanded", "false");
      document.body.classList.remove("no-scroll");
    };
    
    // Cerrar con botón de cerrar
    const closeBtn = document.querySelector("[data-nav-close]");
    if (closeBtn) {
      closeBtn.addEventListener("click", closeMenu);
    }
    
    // Cerrar al hacer click fuera del menú (en el overlay)
    document.addEventListener("click", (e) => {
      if (navLinks.classList.contains("open") && 
          !navLinks.contains(e.target) && 
          !navToggle.contains(e.target) &&
          window.innerWidth <= 768) {
        closeMenu();
      }
    });
    
    // Cerrar con tecla Escape
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && navLinks.classList.contains("open")) {
        closeMenu();
      }
    });

    navLinkItems.forEach((link) => {
      link.addEventListener("click", (e) => {
        // No cerrar el menú si el link tiene un dropdown y estamos en móvil
        const parentItem = link.closest(".nav-item.has-dropdown");
        if (parentItem && window.innerWidth <= 1024) {
          // Si es el toggle link de un dropdown, no hacer nada (ya se maneja arriba)
          if (parentItem.querySelector("a:first-of-type") === link) {
            return; // Ya se maneja en el handler de dropdown
          }
        }
        navLinks.classList.remove("open");
        navToggle.setAttribute("aria-expanded", "false");
        document.body.classList.remove("no-scroll");
      });
    });
  }

  // Dropdown menu functionality
  const dropdownItems = document.querySelectorAll(".nav-item.has-dropdown");
  dropdownItems.forEach((item) => {
    // Get the first direct child <a> element (the toggle link)
    const dropdownToggle = item.children[0]?.tagName === "A" ? item.children[0] : item.querySelector("a:first-of-type");
    const dropdownMenu = item.querySelector(".dropdown-menu");
    // Get direct links (not in sub-menus)
    const allLinks = dropdownMenu?.querySelectorAll("a");
    const dropdownLinks = allLinks ? Array.from(allLinks).filter(link => {
      // Only include links that are direct children of dropdown-menu > li (not in sub-menus)
      const parent = link.parentElement;
      return parent && parent.parentElement === dropdownMenu;
    }) : null;

    if (!dropdownToggle || !dropdownMenu) return;

    // Click handler for mobile (only on the toggle link, not sub-menu links)
    dropdownToggle.addEventListener("click", (e) => {
      // En móvil, siempre prevenir navegación y solo abrir/cerrar submenú
      if (window.innerWidth <= 1024) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        const isExpanded = item.getAttribute("aria-expanded") === "true";
        item.setAttribute("aria-expanded", String(!isExpanded));
        // No navegar, solo abrir/cerrar submenú
        return false;
      }
    }, true); // Usar capture phase para interceptar antes que otros handlers

    // Close dropdown when clicking on direct links (mobile)
    if (dropdownLinks) {
      dropdownLinks.forEach((link) => {
        link.addEventListener("click", () => {
          if (window.innerWidth <= 1024) {
            // Close mobile menu after clicking a link
            const navLinks = document.querySelector("[data-nav-links]");
            const navToggle = document.querySelector("[data-nav-toggle]");
            if (navLinks) navLinks.classList.remove("open");
            if (navToggle) navToggle.setAttribute("aria-expanded", "false");
            document.body.classList.remove("no-scroll");
          }
          // Allow navigation to proceed normally
        });
      });
    }
  });

  // Nested dropdown menu (sub-menu) functionality
  const subDropdownItems = document.querySelectorAll(".nav-item.has-dropdown-sub");
  subDropdownItems.forEach((item) => {
    // Get the first direct child <a> element (the toggle link)
    const subDropdownToggle = item.children[0]?.tagName === "A" ? item.children[0] : item.querySelector("a:first-of-type");
    const subDropdownMenu = item.querySelector(".dropdown-menu-sub");
    const subDropdownLinks = subDropdownMenu?.querySelectorAll("a");

    if (!subDropdownToggle || !subDropdownMenu) return;

    // Click handler for mobile
    subDropdownToggle.addEventListener("click", (e) => {
      if (window.innerWidth <= 1024) {
        e.preventDefault();
        const isExpanded = item.getAttribute("aria-expanded") === "true";
        item.setAttribute("aria-expanded", String(!isExpanded));
      }
    });

    // Close sub-dropdown when clicking on links (mobile)
    if (subDropdownLinks) {
      subDropdownLinks.forEach((link) => {
        link.addEventListener("click", () => {
          if (window.innerWidth <= 1024) {
            // Close mobile menu after clicking a link
            const navLinks = document.querySelector("[data-nav-links]");
            const navToggle = document.querySelector("[data-nav-toggle]");
            if (navLinks) navLinks.classList.remove("open");
            if (navToggle) navToggle.setAttribute("aria-expanded", "false");
            document.body.classList.remove("no-scroll");
          }
          // Allow navigation to proceed normally
        });
      });
    }
  });

  const currentPage = document.body.dataset.page;
  if (currentPage) {
    document
      .querySelectorAll(`[data-nav-link][href*="${currentPage}"]`)
      .forEach((link) => {
        link.classList.add("active");
        // If this link is in a dropdown, mark parent as active
        const dropdownItem = link.closest(".dropdown-menu");
        if (dropdownItem) {
          const parentNavItem = dropdownItem.closest(".nav-item.has-dropdown");
          if (parentNavItem) {
            parentNavItem.classList.add("active");
          }
        }
      });
  }

  const counterItems = document.querySelectorAll("[data-counter]");
  if (counterItems.length) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.5 }
    );

    counterItems.forEach((counter) => observer.observe(counter));
  }

  function animateCounter(element) {
    const target = Number(element.dataset.counter || 0);
    const suffix = element.dataset.suffix || "+";
    const duration = 1200;
    const start = performance.now();

    function update(now) {
      const progress = Math.min((now - start) / duration, 1);
      const value = Math.floor(progress * target);
      
      // Only add suffix when value equals target, otherwise show just the number
      if (value === target) {
        element.textContent = value.toLocaleString("es-CL") + suffix;
      } else {
        element.textContent = value.toLocaleString("es-CL");
      }
      
      if (progress < 1) requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
  }

  document.querySelectorAll("[data-accordion]").forEach((accordion) => {
    accordion.querySelectorAll("[data-accordion-toggle]").forEach((toggle) => {
      toggle.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        const item = toggle.closest("[data-accordion-item]");
        const content = item?.querySelector("[data-accordion-content]");
        const isOpen = item?.classList.contains("open");

        // Close other accordion items in the same accordion
        accordion
          .querySelectorAll("[data-accordion-item]")
          .forEach((accordionItem) => {
            if (accordionItem !== item) {
              accordionItem.classList.remove("open");
              const c = accordionItem.querySelector("[data-accordion-content]");
              if (c) {
                c.style.maxHeight = "";
                c.style.display = "none";
              }
            }
          });

        // Toggle current item
        if (item && content) {
          if (isOpen) {
            // Close
            item.classList.remove("open");
            content.style.maxHeight = "";
            setTimeout(() => {
              content.style.display = "none";
            }, 350);
          } else {
            // Open
            content.style.display = "block";
            item.classList.add("open");
            // Use requestAnimationFrame to ensure display: block is applied before setting maxHeight
            requestAnimationFrame(() => {
              content.style.maxHeight = `${content.scrollHeight}px`;
            });
          }
        }
      });
    });
  });

  document.querySelectorAll("[data-tabs]").forEach((tabs) => {
    const tabButtons = tabs.querySelectorAll("[role=tab]");
    const tabPanels = tabs.querySelectorAll("[role=tabpanel]");

    tabButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const target = button.getAttribute("aria-controls");

        tabButtons.forEach((btn) => {
          btn.setAttribute("aria-selected", String(btn === button));
          btn.setAttribute("tabindex", btn === button ? "0" : "-1");
        });

        tabPanels.forEach((panel) => {
          panel.classList.toggle("active", panel.id === target);
        });
      });
    });
  });

  const toast = document.querySelector("[data-toast]");
  const forms = document.querySelectorAll("form[data-toast-success]");
  if (toast && forms.length) {
    forms.forEach((form) => {
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        toast.textContent = form.dataset.toastSuccess || "Mensaje enviado correctamente.";
        toast.classList.add("show");
        setTimeout(() => toast.classList.remove("show"), 4000);
        form.reset();
      });
    });
  }

  // Inicializar todos los carruseles hero (imágenes y tarjetas destacadas)
  document.querySelectorAll("[data-hero-slider]").forEach((heroSlider) => {
    const track = heroSlider;
    const slides = Array.from(heroSlider.querySelectorAll("[data-hero-slide]")).sort(
      (a, b) => Number(a.dataset.heroOrder || 0) - Number(b.dataset.heroOrder || 0)
    );
    // Buscar dotsContainer dentro del heroSlider o en el contenedor padre
    let dotsContainer = heroSlider.querySelector("[data-hero-dots]");
    if (!dotsContainer) {
      // Si no está dentro, buscar en el contenedor padre
      const parent = heroSlider.parentElement;
      if (parent) {
        dotsContainer = parent.querySelector("[data-hero-dots]");
      }
    }
    if (!slides.length) return;
    
    // Si solo hay un slide, no necesitamos dots ni autoplay
    if (slides.length === 1) {
      slides[0].classList.add("is-active");
      // Reproducir video si es video (solo la primera vez)
      const video = slides[0].querySelector('video');
      if (video && video.dataset.videoAutoplay === 'true') {
        const videoKey = `video_played_${window.location.pathname}_${video.src}`;
        const hasPlayed = sessionStorage.getItem(videoKey);
        if (!hasPlayed) {
          video.play().catch(e => {
            console.log('Autoplay bloqueado:', e);
          });
          // Marcar como reproducido cuando termine
          video.addEventListener('ended', () => {
            sessionStorage.setItem(videoKey, 'true');
          }, { once: true });
        } else {
          // Si ya se reprodujo, asegurar que esté pausado
          video.pause();
        }
      }
      return;
    }
    
    // Si hay más de un slide pero no hay dotsContainer, crear uno
    if (!dotsContainer) {
      const parent = heroSlider.parentElement;
      if (parent) {
        dotsContainer = document.createElement('div');
        dotsContainer.className = 'hero-dots';
        dotsContainer.setAttribute('role', 'presentation');
        dotsContainer.setAttribute('data-hero-dots', '');
        parent.appendChild(dotsContainer);
      } else {
        return; // No podemos continuar sin contenedor para dots
      }
    }

    slides.forEach((slide) => {
      slide.classList.remove("is-active");
      // Pausar videos que no están activos
      const video = slide.querySelector('video');
      if (video) {
        video.pause();
        video.currentTime = 0;
      }
      // Solo insertar antes de dotsContainer si está dentro del track
      if (dotsContainer.parentElement === track) {
        track.insertBefore(slide, dotsContainer);
      }
    });
    slides[0].classList.add("is-active");
    // Reproducir el primer video si es video (solo la primera vez)
    const firstVideo = slides[0].querySelector('video');
    if (firstVideo && firstVideo.dataset.videoAutoplay === 'true') {
      const videoKey = `video_played_${window.location.pathname}_${firstVideo.src}`;
      const hasPlayed = sessionStorage.getItem(videoKey);
      if (!hasPlayed) {
        // Prevenir que se reproduzca automáticamente si el usuario vuelve a la pestaña
        firstVideo.addEventListener('play', () => {
          // Si el video se reproduce automáticamente (no por click del usuario), marcar como reproducido
          const wasUserInitiated = firstVideo.currentTime === 0;
          if (wasUserInitiated) {
            sessionStorage.setItem(videoKey, 'true');
          }
        }, { once: true });
        
        firstVideo.play().catch(e => {
          console.log('Autoplay bloqueado en primer video:', e);
        });
        // Marcar como reproducido cuando termine
        firstVideo.addEventListener('ended', () => {
          sessionStorage.setItem(videoKey, 'true');
        }, { once: true });
      } else {
        // Si ya se reprodujo, asegurar que esté pausado
        firstVideo.pause();
      }
    }

    dotsContainer.innerHTML = "";
    const dots = Array.from(slides).map((slide, slideIndex) => {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.className = "hero-dot" + (slideIndex === 0 ? " is-active" : "");
      dot.setAttribute("aria-label", `Ver imagen: ${slide.dataset.heroLabel || slideIndex + 1}`);
      dot.dataset.heroDot = "";
      dot.dataset.dotIndex = slideIndex;
      dotsContainer.appendChild(dot);
      return dot;
    });

    const interval = Number(heroSlider.dataset.heroInterval) || 6000;
    let index = 0;
    let timer;

    const setActiveSlide = (nextIndex) => {
      // Pausar video anterior si existe
      const prevSlide = slides[index];
      const prevVideo = prevSlide?.querySelector('video');
      if (prevVideo) {
        prevVideo.pause();
        prevVideo.currentTime = 0;
      }
      
      slides[index].classList.remove("is-active");
      dots[index].classList.remove("is-active");
      index = nextIndex;
      slides[index].classList.add("is-active");
      dots[index].classList.add("is-active");
      
      // Reproducir video nuevo si existe (solo si el usuario lo activa manualmente)
      const nextVideo = slides[index].querySelector('video');
      if (nextVideo) {
        // Solo reproducir si el usuario cambió manualmente (no en autoplay del slider)
        // Los videos se reproducirán cuando el usuario haga click en play
        // No forzamos autoplay en cambios de slide
      }
    };

    const startAutoPlay = () => {
      stopAutoPlay();
      timer = setInterval(() => {
        const next = (index + 1) % slides.length;
        setActiveSlide(next);
      }, interval);
    };

    const stopAutoPlay = () => {
      if (timer) clearInterval(timer);
    };

    dots.forEach((dot, dotIndex) => {
      dot.addEventListener("click", () => {
        if (dotIndex === index) return;
        setActiveSlide(dotIndex);
        startAutoPlay();
      });
    });

    heroSlider.addEventListener("mouseenter", stopAutoPlay);
    heroSlider.addEventListener("mouseleave", startAutoPlay);
    
    startAutoPlay();
  });

  // Listener global único para controlar videos cuando cambia la visibilidad de la pestaña
  if (!window.videoVisibilityHandlerAdded) {
    // Prevenir autoplay cuando vuelves a la pestaña
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        // Pausar todos los videos cuando la pestaña no está visible
        document.querySelectorAll('video').forEach(video => {
          if (!video.paused) {
            video.pause();
          }
        });
      } else {
        // Cuando vuelves a la pestaña, prevenir autoplay solo si el video ya se reprodujo
        // Esperar un momento para ver si el usuario está interactuando
        setTimeout(() => {
          document.querySelectorAll('video[data-video-autoplay="true"]').forEach(video => {
            const videoKey = `video_played_${window.location.pathname}_${video.src}`;
            const hasPlayed = sessionStorage.getItem(videoKey);
            // Solo pausar si ya se reprodujo Y el video comenzó a reproducirse automáticamente
            // Si el usuario le dio play manualmente después de volver, no interferir
            if (hasPlayed) {
              // Verificar si el video estaba reproduciéndose antes de cambiar de pestaña
              const wasPlayingBeforeHidden = video.dataset.wasPlaying === 'true';
              // Si NO estaba reproduciéndose antes y ahora está reproduciéndose, es autoplay no deseado
              if (!wasPlayingBeforeHidden && !video.paused) {
                video.pause();
                video.currentTime = 0;
              }
            }
          });
        }, 200);
      }
    });
    
    // Marcar videos que estaban reproduciéndose antes de cambiar de pestaña
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        document.querySelectorAll('video').forEach(video => {
          video.dataset.wasPlaying = video.paused ? 'false' : 'true';
        });
      }
    });
    
    window.videoVisibilityHandlerAdded = true;
  }
  
  // Listener adicional para prevenir reproducción automática no deseada
  // Se ejecuta después de que todos los hero sliders se inicialicen
  setTimeout(() => {
    document.querySelectorAll('video[data-video-autoplay="true"]').forEach(video => {
      const videoKey = `video_played_${window.location.pathname}_${video.src}`;
      const hasPlayed = sessionStorage.getItem(videoKey);
      
      if (hasPlayed) {
        // Si ya se reprodujo, solo asegurar que esté pausado al inicio
        // No bloquear reproducción manual del usuario
        if (!video.paused) {
          video.pause();
          video.currentTime = 0;
        }
      }
    });
  }, 500);

  document.querySelectorAll("[data-carousel]").forEach((carousel) => {
    const track = carousel.querySelector("[data-carousel-track]");
    const prev = carousel.querySelector("[data-carousel-prev]");
    const next = carousel.querySelector("[data-carousel-next]");

    if (!track || !prev || !next) return;

    const updateButtons = () => {
      const maxScroll = track.scrollWidth - track.clientWidth;
      prev.disabled = track.scrollLeft <= 0;
      next.disabled = track.scrollLeft >= maxScroll - 1;
    };

    prev.addEventListener("click", () => {
      track.scrollBy({ left: -track.clientWidth, behavior: "smooth" });
    });

    next.addEventListener("click", () => {
      track.scrollBy({ left: track.clientWidth, behavior: "smooth" });
    });

    track.addEventListener("scroll", updateButtons);
    window.addEventListener("resize", updateButtons);
    updateButtons();
  });
});
const nav = document.querySelector(".navbar");
const body = document.body;
const burger = document.querySelector(".burger");
const navLinks = document.querySelector(".nav-links");

const toggleNav = () => {
  body.classList.toggle("mobile-nav-open");
  const expanded = burger.getAttribute("aria-expanded") === "true";
  burger.setAttribute("aria-expanded", String(!expanded));
  if (!expanded) {
    navLinks.querySelector("a").focus({ preventScroll: true });
  } else {
    burger.focus({ preventScroll: true });
  }
};

if (burger) {
  burger.addEventListener("click", toggleNav);
  burger.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggleNav();
    }
  });
}

navLinks?.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    if (body.classList.contains("mobile-nav-open")) {
      toggleNav();
    }
  });
});

// Shadow on scroll for navbar clarity
const handleScroll = () => {
  if (!nav) return;
  if (window.scrollY > 10) {
    nav.classList.add("navbar-shadow");
  } else {
    nav.classList.remove("navbar-shadow");
  }
};

handleScroll();
window.addEventListener("scroll", handleScroll);

// Removed duplicate counter function - using the one inside DOMContentLoaded instead

// Tabbed panels - Sistema con data-tabs (nuevo)
document.querySelectorAll("[data-tabs]").forEach((tabs) => {
  // Intentar primero con data-tab-button (sistema nuevo)
  let buttons = Array.from(tabs.querySelectorAll("[data-tab-button]"));
  let panels = Array.from(tabs.querySelectorAll("[data-tab-panel]"));
  
  // Si no encuentra, usar sistema con role="tab" (servicios.html)
  if (buttons.length === 0) {
    buttons = Array.from(tabs.querySelectorAll("button[role='tab']"));
    panels = Array.from(tabs.querySelectorAll("[role='tabpanel']"));
  }

  if (buttons.length === 0 || panels.length === 0) return;

  const activate = (buttonId) => {
    buttons.forEach((btn) => {
      let isActive = false;
      
      // Sistema nuevo con data-tab-button
      if (btn.dataset.tabButton) {
        isActive = btn.dataset.tabButton === buttonId;
      } 
      // Sistema con role="tab" (servicios.html)
      else if (btn.getAttribute("role") === "tab") {
        const panelId = btn.getAttribute("aria-controls");
        isActive = panelId === buttonId;
      }
      
      btn.classList.toggle("is-active", isActive);
      btn.setAttribute("aria-selected", String(isActive));
      btn.setAttribute("tabindex", isActive ? "0" : "-1");
    });

    panels.forEach((panel) => {
      let isActive = false;
      
      // Sistema nuevo con data-tab-panel
      if (panel.dataset.tabPanel) {
        isActive = panel.dataset.tabPanel === buttonId;
      }
      // Sistema con role="tabpanel" (servicios.html)
      else if (panel.getAttribute("role") === "tabpanel") {
        isActive = panel.id === buttonId;
      }
      
      panel.classList.toggle("active", isActive);
      panel.hidden = !isActive;
    });
  };

  // Función para centrar la pestaña activa en móvil
  const scrollTabIntoView = (activeButton) => {
    if (window.innerWidth <= 768 && tabs) {
      const tabList = tabs.querySelector('.tab-list');
      if (tabList && activeButton) {
        const tabListRect = tabList.getBoundingClientRect();
        const buttonRect = activeButton.getBoundingClientRect();
        const scrollLeft = tabList.scrollLeft;
        const buttonLeft = buttonRect.left - tabListRect.left + scrollLeft;
        const buttonWidth = buttonRect.width;
        const tabListWidth = tabListRect.width;
        const centerPosition = buttonLeft - (tabListWidth / 2) + (buttonWidth / 2);
        
        tabList.scrollTo({
          left: centerPosition,
          behavior: 'smooth'
        });
      }
    }
  };

  buttons.forEach((button) => {
    button.addEventListener("click", (e) => {
      e.preventDefault();
      let targetId = null;
      
      // Sistema nuevo
      if (button.dataset.tabButton) {
        targetId = button.dataset.tabButton;
      }
      // Sistema con role="tab"
      else if (button.getAttribute("role") === "tab") {
        targetId = button.getAttribute("aria-controls");
      }
      
      if (targetId) {
        activate(targetId);
        
        // Centrar la pestaña activa en móvil
        if (window.innerWidth <= 768) {
          setTimeout(() => {
            scrollTabIntoView(button);
          }, 50);
        }
        
        // Scroll suave al panel en móvil (opcional, puede ser molesto)
        // if (window.innerWidth <= 768) {
        //   const panel = document.getElementById(targetId);
        //   if (panel) {
        //     setTimeout(() => {
        //       panel.scrollIntoView({ behavior: "smooth", block: "start" });
        //     }, 200);
        //   }
        // }
      }
    });
    
    button.addEventListener("keydown", (event) => {
      if (!["ArrowRight", "ArrowLeft"].includes(event.key)) return;
      event.preventDefault();
      const index = buttons.indexOf(button);
      const offset = event.key === "ArrowRight" ? 1 : -1;
      const nextButton = buttons[(index + offset + buttons.length) % buttons.length];
      nextButton.focus();
      
      let targetId = null;
      if (nextButton.dataset.tabButton) {
        targetId = nextButton.dataset.tabButton;
      } else if (nextButton.getAttribute("role") === "tab") {
        targetId = nextButton.getAttribute("aria-controls");
      }
      
      if (targetId) activate(targetId);
    });
  });

  // Activar el primer tab por defecto
  if (buttons.length) {
    const firstButton = buttons[0];
    let targetId = null;
    
    if (firstButton.dataset.tabButton) {
      targetId = firstButton.dataset.tabButton;
    } else if (firstButton.getAttribute("role") === "tab") {
      targetId = firstButton.getAttribute("aria-controls");
    }
    
    if (targetId) {
      activate(targetId);
      // Centrar la primera pestaña en móvil al cargar
      if (window.innerWidth <= 768) {
        setTimeout(() => {
          scrollTabIntoView(firstButton);
        }, 100);
      }
    }
  }
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", (event) => {
    const targetId = anchor.getAttribute("href").slice(1);
    if (!targetId) return;
    const target = document.getElementById(targetId);
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

// Social carousel controls for embedded posts
document.querySelectorAll("[data-social-carousel]").forEach((carousel) => {
  const track = carousel.querySelector("[data-social-track]");
  const prev = carousel.querySelector("[data-social-prev]");
  const next = carousel.querySelector("[data-social-next]");

  if (!track || !prev || !next) return;

  const slideWidth = () => track.firstElementChild?.getBoundingClientRect().width || 320;

  const updateButtons = () => {
    const maxScroll = track.scrollWidth - track.clientWidth - 4;
    prev.disabled = track.scrollLeft <= 4;
    next.disabled = track.scrollLeft >= maxScroll;
  };

  prev.addEventListener("click", () => {
    track.scrollBy({ left: -slideWidth(), behavior: "smooth" });
  });

  next.addEventListener("click", () => {
    track.scrollBy({ left: slideWidth(), behavior: "smooth" });
  });

  track.addEventListener("scroll", updateButtons, { passive: true });
  window.addEventListener("resize", updateButtons);

  updateButtons();
});

// Infinite Carousel - debe ejecutarse independientemente del timeline
document.addEventListener("DOMContentLoaded", () => {
  // Infinite Carousel
  const infiniteCarousels = document.querySelectorAll("[data-carousel-infinite]");
  console.log("Found infinite carousels:", infiniteCarousels.length);
  
  infiniteCarousels.forEach((carousel, carouselIndex) => {
    const track = carousel.querySelector("[data-carousel-track-infinite]");
    const prevBtn = carousel.querySelector("[data-carousel-prev-infinite]");
    const nextBtn = carousel.querySelector("[data-carousel-next-infinite]");
    const autoplayEnabled = carousel.dataset.autoplay === "true";
    const autoplaySpeed = parseInt(carousel.dataset.autoplaySpeed || "4000", 10);
    const itemsPerView = parseInt(carousel.dataset.itemsPerView || "4", 10);
    const continuousScroll = carousel.dataset.continuousScroll === "true"; // Solo para carruseles de logos

    console.log(`Carousel ${carouselIndex}:`, { 
      track: !!track, 
      prevBtn: !!prevBtn, 
      nextBtn: !!nextBtn,
      autoplayEnabled,
      autoplaySpeed,
      itemsPerView
    });

    if (!track) {
      console.warn("Carousel track not found", carousel);
      return;
    }

    const originalItems = Array.from(track.children);
    if (originalItems.length === 0) {
      console.warn("Carousel has no items", carousel);
      return;
    }
    
    console.log(`Carousel ${carouselIndex} has ${originalItems.length} items`);

    const totalItems = originalItems.length;
    
    // Don't initialize carousel if we have no items
    if (totalItems === 0) return;
    
    // Marcar elementos originales para poder ocultar clones en móvil
    originalItems.forEach((item, index) => {
      item.setAttribute('data-carousel-original', 'true');
      item.setAttribute('data-carousel-index', index);
    });
    
    // Detectar si estamos en móvil
    const isMobile = () => window.innerWidth <= 768;
    
    // Variables para clones (necesarias para desktop)
    let cloneCount = 0;
    let beginningCloneCount = 0;
    
    // Solo clonar si NO estamos en móvil
    if (!isMobile()) {
      // For very few items, clone more times to ensure smooth infinite scroll
      // Always clone at least enough for seamless scrolling
      cloneCount = totalItems <= itemsPerView ? 6 : 4;
      beginningCloneCount = totalItems <= itemsPerView ? 4 : 3;

      // Clone items multiple times for seamless infinite effect
      // Clone more copies when we have few items to ensure smooth scrolling
      for (let i = 0; i < cloneCount; i++) {
        originalItems.forEach((item) => {
          const clone = item.cloneNode(true);
          clone.removeAttribute('data-carousel-original');
          track.appendChild(clone);
        });
      }
      
      // Clone items at the beginning (reversed order for going backwards)
      for (let i = 0; i < beginningCloneCount; i++) {
        const reversedItems = [...originalItems].reverse();
        reversedItems.forEach((item) => {
          const clone = item.cloneNode(true);
          clone.removeAttribute('data-carousel-original');
          track.insertBefore(clone, track.firstChild);
        });
      }
    }

    // Start position: en móvil empezar en 0, en desktop después de los clones
    let currentIndex = isMobile() ? 0 : (totalItems * beginningCloneCount);
    let autoplayInterval = null;
    let animationFrameId = null;
    let lastFrameTime = null;
    let isTransitioning = false;
    let resetTimeout = null;
    const scrollSpeed = continuousScroll ? 0.1 : 0.3; // Velocidad más lenta para movimiento continuo (solo logos)

    function getItemsPerView() {
      const width = window.innerWidth;
      if (width <= 768) return 3; // En móvil mostrar 3 elementos a la vez
      if (width <= 900) return 2;
      if (width <= 1200) return 3;
      return itemsPerView;
    }
    
    // Función para actualizar estado de botones
    function updateButtons() {
      if (!prevBtn || !nextBtn) {
        console.warn(`Carousel ${carouselIndex}: Buttons not found in updateButtons`);
        return;
      }
      
      const itemsPerView = getItemsPerView();
      
      // En móvil, usar lógica diferente
      if (window.innerWidth <= 768) {
        const mobileItemsPerView = 3;
        const maxIndex = Math.max(0, totalItems - mobileItemsPerView);
        prevBtn.disabled = currentIndex <= 0;
        // En móvil, permitir avanzar hasta el último grupo completo
        nextBtn.disabled = currentIndex >= maxIndex;
        console.log(`Carousel ${carouselIndex} (mobile): currentIndex=${currentIndex}, maxIndex=${maxIndex}, nextBtn.disabled=${nextBtn.disabled}`);
        return;
      }
      
      // En desktop, los botones NUNCA están deshabilitados porque es infinito
      // El carrusel infinito siempre permite avanzar/retroceder
      prevBtn.disabled = false;
      nextBtn.disabled = false;
      console.log(`Carousel ${carouselIndex} (desktop): Infinite carousel - both buttons enabled (${totalItems} items, ${itemsPerView} per view)`);
    }
    
    // Función para actualizar visibilidad en móvil (mostrar grupo de 3)
    function updateMobileVisibility() {
      if (window.innerWidth > 768) return; // Solo en móvil
      
      const originalItems = Array.from(track.querySelectorAll('[data-carousel-original="true"]'));
      if (originalItems.length === 0) return;
      
      const itemsPerView = 3;
      // currentIndex representa el índice del primer elemento visible
      const startIndex = currentIndex % totalItems;
      
      originalItems.forEach((item, index) => {
        // Calcular qué elementos deben estar visibles (grupos de 3)
        let relativeIndex = (index - startIndex + totalItems) % totalItems;
        if (relativeIndex < itemsPerView) {
          item.style.display = 'block';
          item.style.opacity = '1';
          item.style.visibility = 'visible';
        } else {
          item.style.display = 'none';
        }
      });
    }

    function getItemWidth() {
      const wrapper = track.parentElement;
      if (!wrapper || wrapper.offsetWidth === 0) {
        // Fallback if wrapper not ready
        return 300; // Default item width
      }
      const gap = 24; // 1.5rem = 24px
      const itemsShown = getItemsPerView();
      const calculatedWidth = (wrapper.offsetWidth - (gap * (itemsShown - 1))) / itemsShown;
      return calculatedWidth > 0 ? calculatedWidth : 300;
    }

    function updateTransform(instant = false) {
      // En móvil, usar sistema de visibilidad en lugar de transform
      if (window.innerWidth <= 768) {
        updateMobileVisibility();
        return;
      }
      
      const itemWidth = getItemWidth();
      if (itemWidth <= 0 || isNaN(itemWidth)) {
        // If width not ready, retry after a short delay
        setTimeout(() => updateTransform(instant), 100);
        return;
      }
      const gap = 24;
      const offset = -(currentIndex * (itemWidth + gap));
      
      if (instant) {
        track.style.transition = "none";
        track.style.transform = `translateX(${offset}px)`;
        // Force reflow
        track.offsetHeight;
        requestAnimationFrame(() => {
          track.style.transition = "transform 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)";
        });
      } else {
        // Ensure transition is set for smooth animation
        if (!track.style.transition || track.style.transition === "none") {
          track.style.transition = "transform 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)";
        }
        track.style.transform = `translateX(${offset}px)`;
      }
    }
    
    // Función para actualizar visibilidad en móvil (mostrar grupo de 3)
    function updateMobileVisibility() {
      if (window.innerWidth > 768) return; // Solo en móvil
      
      const originalItems = Array.from(track.querySelectorAll('[data-carousel-original="true"]'));
      if (originalItems.length === 0) {
        // Si no hay elementos aún, reintentar después de un breve delay
        setTimeout(() => updateMobileVisibility(), 100);
        return;
      }
      
      const itemsPerView = 3;
      // currentIndex representa el índice del primer elemento visible
      const startIndex = currentIndex % totalItems;
      
      originalItems.forEach((item, index) => {
        // Calcular qué elementos deben estar visibles (grupos de 3)
        let relativeIndex = (index - startIndex + totalItems) % totalItems;
        if (relativeIndex < itemsPerView) {
          item.style.setProperty('display', 'block', 'important');
          item.style.setProperty('opacity', '1', 'important');
          item.style.setProperty('visibility', 'visible', 'important');
        } else {
          item.style.setProperty('display', 'none', 'important');
        }
      });
      
      // Actualizar botones
      updateButtons();
    }

    function nextSlide() {
      if (isTransitioning) {
        console.log(`Carousel ${carouselIndex}: Already transitioning, ignoring nextSlide`);
        return;
      }
      
      // NO verificar disabled aquí - permitir que funcione siempre en desktop
      // Solo verificar en móvil donde realmente hay límites
      if (window.innerWidth <= 768 && nextBtn && nextBtn.disabled) {
        console.log(`Carousel ${carouselIndex}: Next button disabled on mobile, ignoring`);
        return;
      }
      
      console.log(`Carousel ${carouselIndex}: Executing nextSlide, currentIndex=${currentIndex}`);
      isTransitioning = true;
      stopAutoplay(); // Stop autoplay when manually navigating
      
      // En móvil, avanzar de 3 en 3
      if (window.innerWidth <= 768) {
        const itemsPerView = 3;
        const maxIndex = Math.max(0, totalItems - itemsPerView);
        const newIndex = Math.min(currentIndex + itemsPerView, maxIndex);
        if (newIndex === currentIndex) {
          // No hay más elementos para avanzar
          isTransitioning = false;
          return;
        }
        currentIndex = newIndex;
        updateTransform();
        updateButtons(); // Actualizar estado de botones después de mover
        setTimeout(() => {
          isTransitioning = false;
        }, 300);
        return;
      }
      
      currentIndex++;
      updateTransform();
      updateButtons(); // Actualizar estado de botones después de mover

      // Calculate positions
      // Start position: just after beginning clones (where original items start)
      const startPosition = totalItems * beginningCloneCount;
      // End of original items: just after the original set
      const endOriginal = totalItems * (beginningCloneCount + 1);
      // Total cloned items at the end
      const totalClonedAtEnd = totalItems * cloneCount;
      // Reset threshold: reset when we're about halfway through the end clones
      // This ensures we have plenty of room for seamless reset
      const resetThreshold = endOriginal + Math.floor(totalClonedAtEnd * 0.5);
      
      // When we've moved far enough into the clones, reset seamlessly
      if (currentIndex >= resetThreshold) {
        clearTimeout(resetTimeout);
        resetTimeout = setTimeout(() => {
          // Calculate how many items into the clones we are from endOriginal
          const offsetIntoClones = currentIndex - endOriginal;
          // Reset to start position plus the offset modulo totalItems
          // This ensures seamless transition back to original items
          track.style.transition = "none";
          currentIndex = startPosition + (offsetIntoClones % totalItems);
          updateTransform(true);
          updateButtons(); // Actualizar estado de botones después del reset
          isTransitioning = false;
          
          // Restore transition after reset
          requestAnimationFrame(() => {
            track.style.transition = "";
            if (autoplayEnabled) {
              startAutoplay();
            }
          });
        }, 50); // Very short delay to ensure transition completed
      } else {
        setTimeout(() => {
          isTransitioning = false;
          if (autoplayEnabled) {
            startAutoplay();
          }
        }, 650);
      }
    }

    function prevSlide() {
      if (isTransitioning) return;
      
      // Verificar si el botón está deshabilitado antes de proceder
      if (prevBtn && prevBtn.disabled) return;
      
      isTransitioning = true;
      stopAutoplay(); // Stop autoplay when manually navigating

      // En móvil, retroceder de 3 en 3
      if (window.innerWidth <= 768) {
        const itemsPerView = 3;
        const newIndex = Math.max(currentIndex - itemsPerView, 0);
        if (newIndex === currentIndex) {
          // No hay más elementos para retroceder
          isTransitioning = false;
          return;
        }
        currentIndex = newIndex;
        updateTransform();
        updateButtons(); // Actualizar estado de botones después de mover
        setTimeout(() => {
          isTransitioning = false;
        }, 300);
        return;
      }

      // Calculate positions
      const startPosition = totalItems * beginningCloneCount;
      const endOriginal = totalItems * (beginningCloneCount + 1);
      // Total cloned items at the beginning
      const totalClonedAtStart = totalItems * beginningCloneCount;
      // Reset threshold: when we've gone back far enough into beginning clones
      const resetThreshold = startPosition - Math.floor(totalClonedAtStart * 0.5);

      currentIndex--;
      updateTransform();
      updateButtons(); // Actualizar estado de botones después de mover
      
      // When going backwards and reaching before the start clones, jump to end seamlessly
      if (currentIndex < resetThreshold) {
        // Calculate how far back we went from startPosition
        const offsetBack = startPosition - currentIndex;
        // Calculate equivalent position near the end of original items
        // Use modulo to wrap around if needed
        const equivalentPos = endOriginal - (offsetBack % totalItems);
        currentIndex = equivalentPos > startPosition ? equivalentPos : endOriginal - 1;
        updateTransform();
        updateButtons(); // Actualizar estado de botones después del reset
        
        clearTimeout(resetTimeout);
        resetTimeout = setTimeout(() => {
          // Ensure we're at the correct position
          track.style.transition = "none";
          updateTransform(true);
          updateButtons(); // Actualizar estado de botones después del reset
          isTransitioning = false;
          
          // Restore transition after reset
          requestAnimationFrame(() => {
            track.style.transition = "";
            if (autoplayEnabled) {
              startAutoplay();
            }
          });
        }, 50);
      } else {
        setTimeout(() => {
          isTransitioning = false;
          if (autoplayEnabled) {
            startAutoplay();
          }
        }, 650);
      }
    }

    function startAutoplay() {
      if (!autoplayEnabled) return;
      stopAutoplay();
      // Verify we have valid items before starting autoplay
      if (totalItems === 0) return;
      
      // Si es un carrusel de logos (continuous scroll), usar movimiento continuo
      if (continuousScroll) {
        // Usar requestAnimationFrame para movimiento continuo y suave
        lastFrameTime = performance.now();
      
      function animate(currentTime) {
        if (!autoplayEnabled || isTransitioning) {
          animationFrameId = null;
          return;
        }
        
        if (lastFrameTime === null) {
          lastFrameTime = currentTime;
        }
        
        const deltaTime = currentTime - lastFrameTime;
        lastFrameTime = currentTime;
        
        const itemWidth = getItemWidth();
        const gap = 24;
        const itemWidthWithGap = itemWidth + gap;
        const pixelsToMove = scrollSpeed * deltaTime;
        
        // Obtener el transform actual
        const currentTransform = track.style.transform;
        let currentOffset = 0;
        if (currentTransform) {
          const match = currentTransform.match(/translateX\(([-\d.]+)px\)/);
          if (match) {
            currentOffset = parseFloat(match[1]);
          }
        } else {
          currentOffset = -(currentIndex * itemWidthWithGap);
        }
        
        // Calcular nuevo offset
        const newOffset = currentOffset - pixelsToMove;
        
        // Actualizar currentIndex basado en el offset
        const calculatedIndex = Math.floor(Math.abs(newOffset) / itemWidthWithGap);
        const startPosition = totalItems * beginningCloneCount;
        const endOriginal = totalItems * (beginningCloneCount + 1);
        const totalClonedAtEnd = totalItems * cloneCount;
        const resetThreshold = endOriginal + Math.floor(totalClonedAtEnd * 0.5);
        
        // Si hemos avanzado lo suficiente, actualizar currentIndex
        if (calculatedIndex !== currentIndex && calculatedIndex > currentIndex) {
          currentIndex = calculatedIndex;
          
          // Verificar si necesitamos resetear
          if (currentIndex >= resetThreshold) {
            const offsetIntoClones = currentIndex - endOriginal;
            track.style.transition = "none";
            currentIndex = startPosition + (offsetIntoClones % totalItems);
            const resetOffset = -(currentIndex * itemWidthWithGap);
            track.style.transform = `translateX(${resetOffset}px)`;
            requestAnimationFrame(() => {
              track.style.transition = "";
            });
            animationFrameId = requestAnimationFrame(animate);
            return;
          }
        }
        
        // Movimiento continuo sin transición
        track.style.transition = "none";
        track.style.transform = `translateX(${newOffset}px)`;
        
        animationFrameId = requestAnimationFrame(animate);
      }
      
      animationFrameId = requestAnimationFrame(animate);
      } else {
        // Para carruseles con texto, usar el método original con setInterval
        autoplayInterval = setInterval(() => {
          if (!isTransitioning) {
            nextSlide();
          }
        }, autoplaySpeed);
      }
    }

    function stopAutoplay() {
      if (autoplayInterval) {
        clearInterval(autoplayInterval);
        autoplayInterval = null;
      }
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
      }
      lastFrameTime = null;
      if (resetTimeout) {
        clearTimeout(resetTimeout);
        resetTimeout = null;
      }
    }

    // Event listeners
    if (nextBtn) {
      console.log(`Carousel ${carouselIndex}: Adding next button listener`);
      nextBtn.addEventListener("click", (e) => {
        console.log(`Carousel ${carouselIndex}: Next button clicked, disabled:`, nextBtn.disabled);
        e.preventDefault();
        e.stopPropagation();
        nextSlide();
      });
    } else {
      console.warn(`Carousel ${carouselIndex}: Next button not found!`);
    }

    if (prevBtn) {
      console.log(`Carousel ${carouselIndex}: Adding prev button listener`);
      prevBtn.addEventListener("click", (e) => {
        console.log(`Carousel ${carouselIndex}: Prev button clicked, disabled:`, prevBtn.disabled);
        e.preventDefault();
        e.stopPropagation();
        prevSlide();
      });
    } else {
      console.warn(`Carousel ${carouselIndex}: Prev button not found!`);
    }

    // Pause on hover
    carousel.addEventListener("mouseenter", stopAutoplay);
    carousel.addEventListener("mouseleave", startAutoplay);

    // Handle window resize
    let resizeTimeout;
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        if (window.innerWidth <= 768) {
          // En móvil, reinicializar
          currentIndex = 0;
          updateMobileVisibility();
        } else {
          // En desktop, usar transform
          updateTransform();
        }
        updateButtons();
      }, 250);
    });

    // Initialize - set to start position
    // Wait for DOM and styles to be ready
    const initCarousel = () => {
      // Ensure wrapper has width
      const wrapper = track.parentElement;
      if (!wrapper || wrapper.offsetWidth === 0) {
        setTimeout(initCarousel, 50);
        return;
      }
      
      // En móvil, inicializar currentIndex a 0 y mostrar primeros 3
      if (window.innerWidth <= 768) {
        currentIndex = 0;
        // Pequeño delay para asegurar que los elementos estén en el DOM
        setTimeout(() => {
          updateMobileVisibility();
        }, 100);
      } else {
        // En desktop, usar el sistema de clones
        if (beginningCloneCount > 0) {
          currentIndex = totalItems * beginningCloneCount;
        }
        updateTransform(true);
      }
      
      updateButtons();
      
      // Solo iniciar autoplay si está habilitado y NO estamos en móvil
      if (autoplayEnabled && window.innerWidth > 768) {
        // Small delay to ensure everything is ready
        setTimeout(() => {
          startAutoplay();
        }, 100);
      }
    };
    
    // Try to initialize immediately
    if (document.readyState === "complete") {
      initCarousel();
    } else {
      window.addEventListener("load", initCarousel);
      // Also try with requestAnimationFrame as fallback
      requestAnimationFrame(initCarousel);
    }
  });
});

// Organigrama Accordions - debe ejecutarse independientemente del timeline
document.addEventListener("DOMContentLoaded", () => {
  const orgAccordions = document.querySelectorAll(".org-accordion");
  console.log("Found org accordions:", orgAccordions.length);
  
  orgAccordions.forEach((accordion, index) => {
    const header = accordion.querySelector(".org-accordion-header");
    const content = accordion.querySelector(".org-accordion-content");
    
    console.log(`Accordion ${index}:`, { header: !!header, content: !!content });
    
    if (!header || !content) {
      return;
    }
    
    // Initialize closed state - asegurar que estén cerrados inicialmente
    accordion.setAttribute("aria-expanded", "false");
    header.setAttribute("aria-expanded", "false");
    
    // Establecer estilos iniciales - forzar siempre
    content.style.display = "block"; // Asegurar que esté en display block
    content.style.maxHeight = "0";
    content.style.opacity = "0";
    content.style.overflow = "hidden";
    content.style.transition = "max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease";
    
    header.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      console.log("Accordion clicked:", index);
      
      const isExpanded = accordion.getAttribute("aria-expanded") === "true";
      
      // Toggle current accordion
      if (isExpanded) {
        // Close accordion
        accordion.setAttribute("aria-expanded", "false");
        header.setAttribute("aria-expanded", "false");
        content.style.maxHeight = "0";
        content.style.opacity = "0";
        console.log("Closing accordion:", index);
      } else {
        // Open accordion
        console.log("Opening accordion:", index);
        
        // Asegurar que el contenido sea medible
        content.style.display = "block";
        content.style.maxHeight = "none";
        content.style.opacity = "1";
        content.style.overflow = "visible";
        
        // Forzar reflow
        const height = content.offsetHeight;
        const scrollHeight = content.scrollHeight;
        
        console.log("Content dimensions:", { height, scrollHeight });
        
        // Resetear para animar
        content.style.maxHeight = "0";
        content.style.opacity = "0";
        content.style.overflow = "hidden";
        
        // Establecer atributo
        accordion.setAttribute("aria-expanded", "true");
        header.setAttribute("aria-expanded", "true");
        
        // Animar después de asegurar que el reset se aplique
        setTimeout(() => {
          content.style.maxHeight = scrollHeight + "px";
          content.style.opacity = "1";
          content.style.overflow = "visible";
        }, 10);
      }
    });
  });
});

// Timeline animations and autoplay
document.addEventListener("DOMContentLoaded", () => {
  const timeline = document.querySelector(".timeline");
  if (!timeline) return;

  const items = timeline.querySelectorAll(".timeline-item");
  if (items.length === 0) return;

  let currentIndex = 0;
  let autoplayInterval = null;
  let isPaused = false;
  const autoplaySpeed = 4000; // 4 segundos

  // Calcular el ancho total del timeline
  const updateTimelineLine = () => {
    if (items.length > 0) {
      const lastItem = items[items.length - 1];
      const firstItem = items[0];
      
      // Obtener posiciones reales de los elementos
      const firstRect = firstItem.getBoundingClientRect();
      const lastRect = lastItem.getBoundingClientRect();
      const timelineRect = timeline.getBoundingClientRect();
      
      // Calcular el scrollLeft para ajustar posiciones relativas
      const scrollLeft = timeline.scrollLeft;
      
      // Calcular desde el centro del primer punto hasta el centro del último punto
      const firstItemCenter = (firstRect.left - timelineRect.left + scrollLeft + firstItem.offsetWidth / 2);
      const lastItemCenter = (lastRect.left - timelineRect.left + scrollLeft + lastItem.offsetWidth / 2);
      
      // Ancho de la línea: desde el primer punto hasta el último punto
      const lineWidth = lastItemCenter - firstItemCenter;
      
      // Ajustar el ancho y posición de inicio de la línea
      timeline.style.setProperty('--line-width', `${lineWidth}px`);
      timeline.style.setProperty('--line-start', `${firstItemCenter}px`);
      
      return { firstItemCenter, lastItemCenter, lineWidth };
    }
    return null;
  };
  
  // Función para animar el scroll sincronizado con la línea
  let scrollAnimationFrame = null;
  let isScrollingAnimated = false;
  
  const animateTimelineScroll = () => {
    if (isScrollingAnimated) return;
    
    const lineInfo = updateTimelineLine();
    if (!lineInfo) return;
    
    const scrollableWidth = timeline.scrollWidth - timeline.clientWidth;
    
    // Si no hay scroll disponible, no hacer nada
    if (scrollableWidth <= 0) return;
    
    // Duración de la animación de la línea (8s según CSS)
    const lineDuration = 8000;
    const startTime = Date.now();
    const startScroll = timeline.scrollLeft;
    isScrollingAnimated = true;
    
    const animateScroll = () => {
      if (!isScrollingAnimated) return;
      
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / lineDuration, 1);
      
      // Usar cubic-bezier para que coincida con la línea CSS (0.4, 0, 0.2, 1)
      // Aproximación de ease-in-out-cubic
      const easedProgress = progress < 0.5
        ? 4 * progress * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 3) / 2;
      
      // Calcular la posición de scroll basada en el progreso
      const targetScroll = startScroll + (scrollableWidth * easedProgress);
      
      // Scroll directo para mejor sincronización
      timeline.scrollLeft = targetScroll;
      
      // Continuar animación si no ha terminado
      if (progress < 1) {
        scrollAnimationFrame = requestAnimationFrame(animateScroll);
      } else {
        // Asegurar scroll al final cuando la línea termine
        timeline.scrollLeft = startScroll + scrollableWidth;
        isScrollingAnimated = false;
        updateTimelineLine();
      }
    };
    
    // Esperar a que comience la animación de la línea (1s de delay según CSS)
    setTimeout(() => {
      animateScroll();
    }, 1000);
  };
  
  // Cancelar animación de scroll si el usuario interactúa manualmente
  timeline.addEventListener('scroll', () => {
    if (isScrollingAnimated) {
      isScrollingAnimated = false;
      if (scrollAnimationFrame) {
        cancelAnimationFrame(scrollAnimationFrame);
        scrollAnimationFrame = null;
      }
    }
  }, { passive: true });
  
  // Inicializar línea al cargar
  setTimeout(() => {
    updateTimelineLine();
  }, 100);

  // Intersection Observer para animaciones iniciales
  const timelineObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          timeline.classList.add("animated");
          
          // Actualizar línea primero
          updateTimelineLine();
          
          // Animate timeline items with stagger - transiciones más lentas y profesionales
          items.forEach((item, index) => {
            setTimeout(() => {
              item.classList.add("visible");
            }, index * 500 + 1000);
          });
          
          // Iniciar scroll sincronizado con la línea azul
          setTimeout(() => {
            animateTimelineScroll();
          }, 500);
          
          // Iniciar autoplay después de que termine la animación de la línea (8s + 1s delay)
          setTimeout(() => {
            updateTimelineLine();
            startAutoplay();
          }, 10000);
          
          timelineObserver.unobserve(timeline);
        }
      });
    },
    { threshold: 0.2 }
  );
  
  timelineObserver.observe(timeline);

  // Función para mover al siguiente item
  const moveToNext = () => {
    if (isPaused) return;
    
    currentIndex = (currentIndex + 1) % items.length;
    const item = items[currentIndex];
    
    // Scroll suave al item
    const itemRect = item.getBoundingClientRect();
    const timelineRect = timeline.getBoundingClientRect();
    const scrollLeft = timeline.scrollLeft;
    const itemLeft = itemRect.left - timelineRect.left + scrollLeft;
    const itemCenter = itemLeft - (timelineRect.width / 2) + (itemRect.width / 2);
    
    timeline.scrollTo({
      left: itemCenter,
      behavior: 'smooth'
    });
  };

  // Iniciar autoplay
  const startAutoplay = () => {
    if (autoplayInterval) return;
    
    autoplayInterval = setInterval(() => {
      moveToNext();
    }, autoplaySpeed);
  };

  // Pausar autoplay
  const pauseAutoplay = () => {
    isPaused = true;
    if (autoplayInterval) {
      clearInterval(autoplayInterval);
      autoplayInterval = null;
    }
  };

  // Reanudar autoplay después de 5 segundos de inactividad
  let pauseTimeout = null;
  const resumeAutoplay = () => {
    isPaused = false;
    if (pauseTimeout) {
      clearTimeout(pauseTimeout);
    }
    pauseTimeout = setTimeout(() => {
      startAutoplay();
    }, 5000);
  };

  // Pausar en hover o interacción
  timeline.addEventListener('mouseenter', pauseAutoplay);
  timeline.addEventListener('mouseleave', resumeAutoplay);
  timeline.addEventListener('touchstart', pauseAutoplay);
  timeline.addEventListener('touchend', () => {
    setTimeout(resumeAutoplay, 5000);
  });

  // Actualizar línea cuando se hace scroll o resize - con debounce para mejor performance
  let resizeTimeout;
  let scrollTimeout;
  
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      updateTimelineLine();
    }, 250);
  });
  
  timeline.addEventListener('scroll', () => {
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(() => {
      updateTimelineLine();
    }, 100);
  }, { passive: true });

  // Timeline item expand/collapse functionality
  const timelineItems = document.querySelectorAll("[data-timeline-item]");
  timelineItems.forEach((item, index) => {
    const header = item.querySelector(".timeline-header");
    const content = item.querySelector(".timeline-content");
    
    if (!header || !content) return;

    header.addEventListener("click", () => {
      const isExpanded = item.getAttribute("aria-expanded") === "true";
      
      // Pausar autoplay cuando se abre una card
      pauseAutoplay();
      
      // Close other items
      timelineItems.forEach((otherItem) => {
        if (otherItem !== item) {
          const otherHeader = otherItem.querySelector(".timeline-header");
          const otherContent = otherItem.querySelector(".timeline-content");
          if (otherHeader && otherContent) {
            otherItem.setAttribute("aria-expanded", "false");
            otherHeader.setAttribute("aria-expanded", "false");
            otherContent.style.maxHeight = "0";
            setTimeout(() => {
              otherContent.style.paddingTop = "0";
              otherContent.style.paddingBottom = "0";
            }, 400);
          }
        }
      });

      // Toggle current item
      if (isExpanded) {
        item.setAttribute("aria-expanded", "false");
        header.setAttribute("aria-expanded", "false");
        content.style.maxHeight = "0";
        setTimeout(() => {
          content.style.paddingTop = "0";
          content.style.paddingBottom = "0";
        }, 400);
        // Reanudar autoplay después de cerrar
        resumeAutoplay();
      } else {
        item.setAttribute("aria-expanded", "true");
        header.setAttribute("aria-expanded", "true");
        content.style.display = "block";
        content.style.paddingTop = "0";
        content.style.paddingBottom = "1.75rem";
        
        // Scroll suave al item expandido - horizontal y vertical
        setTimeout(() => {
          const itemRect = item.getBoundingClientRect();
          const timelineRect = timeline.getBoundingClientRect();
          const scrollLeft = timeline.scrollLeft;
          const scrollTop = timeline.scrollTop;
          
          // Scroll horizontal: centrar el item
          const itemLeft = itemRect.left - timelineRect.left + scrollLeft;
          const itemCenter = itemLeft - (timelineRect.width / 2) + (itemRect.width / 2);
          
          // Scroll vertical: asegurar que el item esté visible
          const isOdd = Array.from(timeline.querySelectorAll('.timeline-item')).indexOf(item) % 2 === 0;
          let verticalOffset = 0;
          
          if (isOdd) {
            // Items impares: asegurar que estén visibles arriba
            const itemTop = itemRect.top - timelineRect.top + scrollTop;
            if (itemTop < 100) {
              verticalOffset = itemTop - 120; // Dejar espacio arriba
            }
          } else {
            // Items pares: asegurar que estén visibles abajo
            const itemBottom = itemRect.bottom - timelineRect.bottom + scrollTop;
            const timelineHeight = timeline.clientHeight;
            if (itemBottom > timelineHeight - 100) {
              verticalOffset = itemBottom - timelineHeight + 120; // Dejar espacio abajo
            }
          }
          
          timeline.scrollTo({
            left: itemCenter,
            top: scrollTop + verticalOffset,
            behavior: 'smooth'
          });
        }, 100);
        
        // Calculate max height based on content
        requestAnimationFrame(() => {
          content.style.maxHeight = `${content.scrollHeight}px`;
        });
        
        // Actualizar índice actual
        currentIndex = index;
      }
    });
  });

});

// Carrusel vertical para publicaciones
document.addEventListener("DOMContentLoaded", () => {
  const verticalCarousels = document.querySelectorAll("[data-vertical-carousel]");
  console.log("Found vertical carousels:", verticalCarousels.length);
  
  if (verticalCarousels.length === 0) {
    console.log("No vertical carousels found, retrying...");
    setTimeout(() => {
      const retryCarousels = document.querySelectorAll("[data-vertical-carousel]");
      if (retryCarousels.length > 0) {
        console.log("Found vertical carousels on retry:", retryCarousels.length);
        initVerticalCarousels(retryCarousels);
      }
    }, 500);
    return;
  }
  
  initVerticalCarousels(verticalCarousels);
});

function initVerticalCarousels(verticalCarousels) {
  verticalCarousels.forEach((carousel, index) => {
    const wrapper = carousel.querySelector(".vertical-carousel-wrapper");
    const track = carousel.querySelector("[data-vertical-carousel-track]");
    const prevBtn = carousel.querySelector("[data-vertical-carousel-prev]");
    const nextBtn = carousel.querySelector("[data-vertical-carousel-next]");
    // Ajustar items por vista según el tamaño de pantalla
    const getItemsPerView = () => {
      return window.innerWidth <= 768 ? 2 : parseInt(carousel.dataset.itemsPerView || "3", 10);
    };
    let itemsPerView = getItemsPerView();
    const autoplayEnabled = carousel.dataset.autoplay === "true";
    const autoplaySpeed = parseInt(carousel.dataset.autoplaySpeed || "4000", 10);

    console.log(`Vertical carousel ${index}:`, {
      wrapper: !!wrapper,
      track: !!track,
      prevBtn: !!prevBtn,
      nextBtn: !!nextBtn,
      itemsPerView: itemsPerView
    });

    if (!track || !prevBtn || !nextBtn || !wrapper) {
      console.warn(`Vertical carousel ${index} missing required elements`);
      return;
    }

    const items = Array.from(track.children);
    console.log(`Vertical carousel ${index} has ${items.length} items`);
    if (items.length === 0) return;

    const totalItems = items.length;
    let currentIndex = 0;
    let autoplayInterval = null;
    const gap = 24; // 1.5rem = 24px

    function getItemHeight() {
      if (items.length === 0) return 0;
      // Calcular altura promedio de los primeros items para mayor precisión
      let totalHeight = 0;
      const itemsToCheck = Math.min(itemsPerView, items.length);
      for (let i = 0; i < itemsToCheck; i++) {
        const item = items[i];
        const height = item.offsetHeight || item.getBoundingClientRect().height;
        totalHeight += height;
      }
      return itemsToCheck > 0 ? Math.ceil(totalHeight / itemsToCheck) : 0;
    }

    function updateWrapperHeight() {
      itemsPerView = getItemsPerView(); // Recalcular según tamaño de pantalla
      
      // Esperar a que los items se rendericen completamente
      if (items.length === 0) return;
      
      // Calcular altura real sumando las alturas de los primeros N items + gaps
      let totalHeight = 0;
      const itemsToShow = Math.min(itemsPerView, items.length);
      
      for (let i = 0; i < itemsToShow; i++) {
        const item = items[i];
        const itemHeight = item.offsetHeight || item.getBoundingClientRect().height;
        totalHeight += itemHeight;
        // Agregar gap solo entre items (no después del último)
        if (i < itemsToShow - 1) {
          totalHeight += gap;
        }
      }
      
      const wrapperHeight = Math.ceil(totalHeight);
      
      if (wrapperHeight > 0 && itemsPerView > 0) {
        // Forzar altura fija para limitar la vista - usar !important a través de setProperty
        wrapper.style.setProperty('height', wrapperHeight + 'px', 'important');
        wrapper.style.setProperty('max-height', wrapperHeight + 'px', 'important');
        wrapper.style.setProperty('min-height', wrapperHeight + 'px', 'important');
        wrapper.style.setProperty('overflow', 'hidden', 'important');
        wrapper.style.setProperty('position', 'relative', 'important');
        wrapper.style.setProperty('display', 'block', 'important');
        
        // Asegurar que el track no se desborde
        track.style.setProperty('position', 'relative', 'important');
        
        console.log(`Vertical carousel ${index}: Setting wrapper height to ${wrapperHeight}px (itemsPerView: ${itemsPerView}, itemsToShow: ${itemsToShow})`);
        
        // Verificar que se aplicó correctamente
        const appliedHeight = wrapper.offsetHeight;
        console.log(`Vertical carousel ${index}: Applied height: ${appliedHeight}px, Expected: ${wrapperHeight}px`);
        if (Math.abs(appliedHeight - wrapperHeight) > 5) {
          // Si no se aplicó correctamente, intentar de nuevo
          setTimeout(() => updateWrapperHeight(), 100);
        }
      } else {
        console.log(`Vertical carousel ${index}: Waiting for items to render (wrapperHeight: ${wrapperHeight}, itemsPerView: ${itemsPerView})`);
        // Si aún no hay altura, reintentar
        setTimeout(() => updateWrapperHeight(), 100);
      }
    }

    function updateTransform(instant = false) {
      const itemHeight = getItemHeight();
      if (itemHeight <= 0) {
        setTimeout(() => updateTransform(instant), 100);
        return;
      }

      const translateY = -(currentIndex * (itemHeight + gap));
      track.style.transition = instant ? "none" : "transform 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)";
      track.style.transform = `translateY(${translateY}px)`;
      track.style.willChange = 'transform';
      
      updateButtons();
    }

    function updateButtons() {
      if (!prevBtn || !nextBtn) return;
      
      const itemsPerView = getItemsPerView();
      
      // En móvil, usar lógica diferente
      if (window.innerWidth <= 768) {
        const mobileItemsPerView = 3;
        const maxIndex = totalItems - mobileItemsPerView;
        prevBtn.disabled = currentIndex <= 0;
        nextBtn.disabled = currentIndex >= maxIndex;
        return;
      }
      
      const maxIndex = Math.max(0, totalItems - itemsPerView);
      prevBtn.disabled = currentIndex <= 0;
      nextBtn.disabled = currentIndex >= maxIndex;
    }

    function goToNext() {
      itemsPerView = getItemsPerView(); // Recalcular
      const maxIndex = Math.max(0, totalItems - itemsPerView);
      if (currentIndex < maxIndex) {
        currentIndex++;
        updateTransform();
      }
    }

    function goToPrev() {
      if (currentIndex > 0) {
        currentIndex--;
        updateTransform();
      }
    }

    function startAutoplay() {
      if (!autoplayEnabled) return;
      stopAutoplay();
      autoplayInterval = setInterval(() => {
        itemsPerView = getItemsPerView(); // Recalcular
        const maxIndex = Math.max(0, totalItems - itemsPerView);
        if (currentIndex >= maxIndex) {
          currentIndex = 0;
        } else {
          currentIndex++;
        }
        updateTransform();
      }, autoplaySpeed);
    }

    function stopAutoplay() {
      if (autoplayInterval) {
        clearInterval(autoplayInterval);
        autoplayInterval = null;
      }
    }

    prevBtn.addEventListener("click", () => {
      goToPrev();
      if (autoplayEnabled) {
        stopAutoplay();
        startAutoplay();
      }
    });

    nextBtn.addEventListener("click", () => {
      goToNext();
      if (autoplayEnabled) {
        stopAutoplay();
        startAutoplay();
      }
    });

    carousel.addEventListener("mouseenter", stopAutoplay);
    carousel.addEventListener("mouseleave", () => {
      if (autoplayEnabled) startAutoplay();
    });

    // Inicializar - esperar a que el DOM esté listo
    function initCarousel() {
      // Esperar a que los elementos se rendericen completamente
      const initInterval = setInterval(() => {
        const itemHeight = getItemHeight();
        if (itemHeight > 0) {
          clearInterval(initInterval);
          // Aplicar altura inmediatamente
          updateWrapperHeight();
          // Esperar un frame para que se aplique
          requestAnimationFrame(() => {
            // Verificar y reaplicar si es necesario
            updateWrapperHeight();
            updateTransform(true);
            updateButtons();
          });
        }
      }, 50);
      
      // Timeout de seguridad
      setTimeout(() => {
        clearInterval(initInterval);
        const itemHeight = getItemHeight();
        if (itemHeight > 0) {
          updateWrapperHeight();
          // Verificar después de aplicar
          setTimeout(() => {
            updateWrapperHeight();
            updateTransform(true);
            updateButtons();
          }, 100);
        }
      }, 1000);
    }
    
    // Ejecutar inicialización
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initCarousel);
    } else {
      initCarousel();
    }
    
    if (autoplayEnabled) {
      setTimeout(() => startAutoplay(), 200);
    }

    // Recalcular en resize
    let resizeTimer;
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        const oldItemsPerView = itemsPerView;
        itemsPerView = getItemsPerView();
        
        // Ajustar índice si es necesario
        const maxIndex = Math.max(0, totalItems - itemsPerView);
        if (currentIndex > maxIndex) {
          currentIndex = maxIndex;
        }
        
        updateWrapperHeight();
        updateTransform(true);
        updateButtons();
      }, 250);
    });

    // Recalcular cuando las imágenes se carguen
    window.addEventListener("load", () => {
      updateWrapperHeight();
      updateTransform(true);
      updateButtons();
    });
  });
}

// ============================================
// GESTOS TÁCTILES PARA CARRUSELES
// ============================================

function initTouchGestures() {
  // Swipe para carruseles infinitos
  const infiniteCarousels = document.querySelectorAll('.infinite-carousel');
  
  infiniteCarousels.forEach(carousel => {
    const track = carousel.querySelector('.carousel-track-infinite');
    const prevBtn = carousel.querySelector('.carousel-nav-btn[data-direction="prev"]');
    const nextBtn = carousel.querySelector('.carousel-nav-btn[data-direction="next"]');
    
    if (!track) return;
    
    let startX = 0;
    let currentX = 0;
    let isDragging = false;
    let startTransform = 0;
    
    track.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
      const transform = window.getComputedStyle(track).transform;
      startTransform = transform === 'none' ? 0 : parseFloat(transform.split(',')[4] || 0);
      isDragging = true;
      track.style.transition = 'none';
    }, { passive: true });
    
    track.addEventListener('touchmove', (e) => {
      if (!isDragging) return;
      currentX = e.touches[0].clientX;
      const diff = currentX - startX;
      track.style.transform = `translateX(${startTransform + diff}px)`;
    }, { passive: true });
    
    track.addEventListener('touchend', () => {
      if (!isDragging) return;
      isDragging = false;
      track.style.transition = '';
      
      const diff = currentX - startX;
      const threshold = 50; // Mínimo de píxeles para activar swipe
      
      if (Math.abs(diff) > threshold) {
        if (diff > 0 && prevBtn) {
          prevBtn.click();
        } else if (diff < 0 && nextBtn) {
          nextBtn.click();
        } else {
          // Resetear posición si no hay suficiente movimiento
          track.style.transform = '';
        }
      } else {
        // Resetear si no hay suficiente movimiento
        track.style.transform = '';
      }
    }, { passive: true });
  });
  
  // Swipe para hero slider
  const heroSliders = document.querySelectorAll('[data-hero-slider]');
  
  heroSliders.forEach(slider => {
    let startX = 0;
    let startY = 0;
    let isDragging = false;
    
    slider.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
      isDragging = true;
    }, { passive: true });
    
    slider.addEventListener('touchmove', (e) => {
      if (!isDragging) return;
      // Prevenir scroll vertical si hay movimiento horizontal significativo
      const diffX = Math.abs(e.touches[0].clientX - startX);
      const diffY = Math.abs(e.touches[0].clientY - startY);
      
      if (diffX > diffY && diffX > 10) {
        e.preventDefault();
      }
    }, { passive: false });
    
    slider.addEventListener('touchend', (e) => {
      if (!isDragging) return;
      isDragging = false;
      
      const endX = e.changedTouches[0].clientX;
      const endY = e.changedTouches[0].clientY;
      const diffX = startX - endX;
      const diffY = startY - endY;
      const threshold = 50;
      
      // Solo procesar si el movimiento horizontal es mayor que el vertical
      if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > threshold) {
        const dots = slider.querySelectorAll('.hero-dot');
        const activeDot = slider.querySelector('.hero-dot.is-active');
        if (!activeDot) return;
        
        const currentIndex = Array.from(dots).indexOf(activeDot);
        
        if (diffX > 0 && currentIndex < dots.length - 1) {
          // Swipe izquierda - siguiente
          dots[currentIndex + 1].click();
        } else if (diffX < 0 && currentIndex > 0) {
          // Swipe derecha - anterior
          dots[currentIndex - 1].click();
        }
      }
    }, { passive: true });
  });
  
  // Swipe para vertical carousel
  const verticalCarousels = document.querySelectorAll('[data-vertical-carousel]');
  
  verticalCarousels.forEach(carousel => {
    const wrapper = carousel.querySelector('.vertical-carousel-wrapper');
    const prevBtn = carousel.querySelector('.vertical-carousel-btn[data-direction="prev"]');
    const nextBtn = carousel.querySelector('.vertical-carousel-btn[data-direction="next"]');
    
    if (!wrapper) return;
    
    let startY = 0;
    let startX = 0;
    let isDragging = false;
    
    wrapper.addEventListener('touchstart', (e) => {
      startY = e.touches[0].clientY;
      startX = e.touches[0].clientX;
      isDragging = true;
    }, { passive: true });
    
    wrapper.addEventListener('touchmove', (e) => {
      if (!isDragging) return;
      const currentY = e.touches[0].clientY;
      const currentX = e.touches[0].clientX;
      const diffY = Math.abs(currentY - startY);
      const diffX = Math.abs(currentX - (startX || currentX));
      
      // Prevenir scroll si hay movimiento vertical significativo
      if (diffY > diffX && diffY > 10) {
        e.preventDefault();
      }
    }, { passive: false });
    
    wrapper.addEventListener('touchend', (e) => {
      if (!isDragging) return;
      isDragging = false;
      
      const endY = e.changedTouches[0].clientY;
      const diffY = startY - endY;
      const threshold = 50;
      
      if (Math.abs(diffY) > threshold) {
        if (diffY > 0 && nextBtn) {
          // Swipe arriba - siguiente
          nextBtn.click();
        } else if (diffY < 0 && prevBtn) {
          // Swipe abajo - anterior
          prevBtn.click();
        }
      }
    }, { passive: true });
  });
}

// Inicializar gestos táctiles
document.addEventListener("DOMContentLoaded", () => {
  initTouchGestures();
});

// Reinicializar después de cambios dinámicos
if (window.MutationObserver) {
  const observer = new MutationObserver(() => {
    initTouchGestures();
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}



