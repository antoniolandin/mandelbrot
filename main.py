import pygame
import moderngl
from array import array

LARGO, ALTO = 1920, 1080
BLANCO = (255, 255, 255)

pygame.init()
pantalla = pygame.display.set_mode((LARGO, ALTO), pygame.OPENGL | pygame.DOUBLEBUF)
display = pygame.Surface(pantalla.get_size())
pygame.display.set_caption("Mandelbrot shader")

ctx = moderngl.create_context()
# fmt: off
buffer = ctx.buffer(data=array("f", [
    -1.0, 1.0, 0.0, 0.0, # arriba izquierda
    1.0, 1.0, 1.0, 0.0, # arriba derecha
    -1.0, -1.0, 0.0, 1.0, # abajo izquierda
    1.0, -1.0, 1.0, 1.0 # abajo derecha
]))
# fmt: on

alto_figura = 2.5
largo_figura = alto_figura * (LARGO / ALTO)

vertex_shader = """
#version 330 core

in vec2 vertices;
in vec2 texcoord;
out vec2 uvs;

void main() {
    uvs = texcoord;
    gl_Position = vec4(vertices, 0.0, 1.0);
}
"""


fragment_shader = """
#version 330 core

uniform float zoom;
uniform vec2 desplazamiento;
uniform float largo_figura;
uniform float alto_figura;
uniform int max_iter;

in vec2 uvs;
out vec4 color;

float mandlebrot(vec2 c) {
    vec2 z = c;
    
    for (int i = 0; i < max_iter; i++) {
        // (a+bi)^2 = (a+bi)(a+bi) = a^2 + abi+ abi - b^2
        float x = z.x*z.x - z.y * z.y;
        float y = 2*z.x*z.y;

        z.x = x + c.x;
        z.y = y + c.y;

        if (length(z) > 2.0) {
            return float(i)/float(max_iter);
        }
    }

    return 1.0;
}

void main() {
    vec2 uvs_centrados = uvs - vec2(0.5,0.5);

    vec2 c = (uvs_centrados * vec2(largo_figura, alto_figura) * zoom) + desplazamiento;     
    float porcentaje = mandlebrot(c);

    color = vec4(0.0, 0.0, 0.0, 1.0);
    if (porcentaje < 1.0) {
        color = vec4(5.0*porcentaje, 2.0*porcentaje, 8.0*porcentaje, 1.0);
    }
}
"""

programa = ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
objeto_render = ctx.vertex_array(programa, [(buffer, "2f 2f", "vertices", "texcoord")])


def superficie_a_texture(superficie: pygame.Surface) -> moderngl.Texture:
    textura = ctx.texture(superficie.get_size(), 4)
    textura.filter = (moderngl.NEAREST, moderngl.NEAREST)
    textura.swizzle = "BGRA"
    textura.write(superficie.get_view("1"))

    return textura


zoom = 1.0
# el desplazamiento original es el centro de la figura en el plano complejo
desplazamiento = [-0.75, 0.0]
arrastrando = False
max_iter = 100

while True:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_q:
                pygame.quit()
                exit()
        elif evento.type == pygame.MOUSEWHEEL:
            zoom_anterior = zoom
            if evento.y > 0:
                zoom /= 1.2
            else:
                zoom *= 1.2
            pos_raton = pygame.mouse.get_pos()

            # normalizar la posición del raton
            x = pos_raton[0] / LARGO
            y = pos_raton[1] / ALTO

            desplazamiento[0] += (x - 0.5) * largo_figura * (zoom_anterior - zoom)
            desplazamiento[1] += (y - 0.5) * alto_figura * (zoom_anterior - zoom)

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:
                arrastrando = True
        elif evento.type == pygame.MOUSEBUTTONUP:
            if evento.button == 1:
                arrastrando = False
        elif evento.type == pygame.MOUSEMOTION:
            if arrastrando:
                # cuanto se ha movido el ratón desde el último fotograma
                dx, dy = evento.rel

                desplazamiento[0] -= (dx / LARGO) * largo_figura * zoom
                desplazamiento[1] -= (dy / ALTO) * alto_figura * zoom

    # asignar uniforms del fragment shader
    programa["zoom"] = zoom
    programa["desplazamiento"] = desplazamiento
    programa["largo_figura"] = largo_figura
    programa["alto_figura"] = alto_figura
    programa["max_iter"] = max_iter

    # RENDER
    objeto_render.render(mode=moderngl.TRIANGLE_STRIP)

    pygame.display.flip()
