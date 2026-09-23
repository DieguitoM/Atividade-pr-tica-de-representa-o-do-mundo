import pygame
import sys
import math
import random
import time

LARGURA_TELA, ALTURA_TELA = 1000, 700
GRID_LINHAS, GRID_COLUNAS = 3, 3
LARGURA_AREA, ALTURA_AREA = 1100, 1100
LARGURA_MUNDO = GRID_COLUNAS * LARGURA_AREA  # 3300 px
ALTURA_MUNDO = GRID_LINHAS * ALTURA_AREA    # 3300 px

FPS = 60


COR_FUNDO = (25, 25, 30)
COR_GRID = (60, 60, 75)
COR_AREA_INATIVA = (35, 35, 42)
COR_AREA_ATIVA = (55, 75, 65)
COR_PLAYER = (50, 160, 255)
COR_DASH = (120, 220, 255)
COR_VERMELHO = (230, 50, 50)
COR_ROXO = (160, 50, 230)
COR_ITEM_VIDA = (50, 220, 100)
COR_ITEM_MUNICAO = (245, 195, 35)
COR_TEXTO = (240, 240, 240)
COR_HUD_BG = (15, 15, 20)


class Camera:
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        self.x = 0
        self.y = 0

    def atualizar(self, alvo_x, alvo_y):
        self.x = max(0, min(alvo_x - self.largura // 2, LARGURA_MUNDO - self.largura))
        self.y = max(0, min(alvo_y - self.altura // 2, ALTURA_MUNDO - self.altura))

    def aplicar(self, obj_x, obj_y):
        return obj_x - self.x, obj_y - self.y



class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.raio = 16
        self.velocidade = 4.5
        self.vida_max = 100
        self.vida = 100
        self.municao_max = 3
        self.municao = 3
        self.dir_x = 0
        self.dir_y = -1  
        

        self.em_dash = False
        self.duracao_dash = 0
        self.velocidade_dash = 18
        self.cooldown_dash = 0          
        self.COOLDOWN_DASH_MAX = 600   
        
        self.cooldown_invuln = 0

    def mover(self, teclas):
        if self.cooldown_dash > 0:
            self.cooldown_dash -= 1

        if self.em_dash:
            self.x += self.dir_x * self.velocidade_dash
            self.y += self.dir_y * self.velocidade_dash
            self.duracao_dash -= 1
            if self.duracao_dash <= 0:
                self.em_dash = False
        else:
            dx, dy = 0, 0
            if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
                dx -= 1
            if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
                dx += 1
            if teclas[pygame.K_UP] or teclas[pygame.K_w]:
                dy -= 1
            if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
                dy += 1

            if dx != 0 or dy != 0:
                norma = math.hypot(dx, dy)
                self.dir_x = dx / norma
                self.dir_y = dy / norma
                self.x += self.dir_x * self.velocidade
                self.y += self.dir_y * self.velocidade

        self.x = max(self.raio, min(LARGURA_MUNDO - self.raio, self.x))
        self.y = max(self.raio, min(ALTURA_MUNDO - self.raio, self.y))

        if self.cooldown_invuln > 0:
            self.cooldown_invuln -= 1

    def usar_dash(self):
        if self.cooldown_dash == 0 and not self.em_dash:
            self.em_dash = True
            self.duracao_dash = 8
            self.cooldown_dash = self.COOLDOWN_DASH_MAX
            return True
        return False

    def atirar(self, tiros):
        if self.municao > 0:
            self.municao -= 1
            tiros.append(Tiro(self.x, self.y, self.dir_x, self.dir_y))
            return True
        return False

    def desenhar(self, tela, camera):
        cx, cy = camera.aplicar(self.x, self.y)
        cor = COR_DASH if self.em_dash else COR_PLAYER
        if self.cooldown_invuln % 4 < 2:
            pygame.draw.circle(tela, cor, (int(cx), int(cy)), self.raio)
            p_frente = (int(cx + self.dir_x * (self.raio + 6)), int(cy + self.dir_y * (self.raio + 6)))
            pygame.draw.line(tela, (255, 255, 255), (cx, cy), p_frente, 3)


class Tiro:
    def __init__(self, x, y, dir_x, dir_y):
        self.x = x
        self.y = y
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.raio = 14
        self.velocidade = 12
        self.dano = 10
        self.distancia_percorrida = 0
        self.alcance_maximo = 144
        self.ativo = True
        self.atingidos = set()  

    def atualizar(self):
        dx = self.dir_x * self.velocidade
        dy = self.dir_y * self.velocidade
        self.x += dx
        self.y += dy
        self.distancia_percorrida += self.velocidade

        if self.distancia_percorrida >= self.alcance_maximo:
            self.ativo = False

    def desenhar(self, tela, camera):
        cx, cy = camera.aplicar(self.x, self.y)
        pygame.draw.circle(tela, (255, 220, 50), (int(cx), int(cy)), self.raio)
        pygame.draw.circle(tela, (255, 255, 255), (int(cx), int(cy)), self.raio - 4)


class InimigoVermelho:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.raio = 14
        self.vida_max = 10
        self.vida = 10
        self.dano_contato = 10
        self.velocidade = 3.9

    def atualizar(self, px, py):
        dx = px - self.x
        dy = py - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += (dx / dist) * self.velocidade
            self.y += (dy / dist) * self.velocidade

    def desenhar(self, tela, camera):
        cx, cy = camera.aplicar(self.x, self.y)
        pygame.draw.circle(tela, COR_VERMELHO, (int(cx), int(cy)), self.raio)
        largura_barra = 24
        pct = max(0, self.vida / self.vida_max)
        pygame.draw.rect(tela, (50, 0, 0), (cx - 12, cy - 22, largura_barra, 4))
        pygame.draw.rect(tela, (255, 50, 50), (cx - 12, cy - 22, largura_barra * pct, 4))


class InimigoRoxo:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.raio = 16
        self.vida_max = 20
        self.vida = 20
        self.dano_contato = 20
        self.velocidade = 4.8
        self.angulo_espiral = random.uniform(0, math.pi * 2)

    def atualizar(self, px, py):
        dx = px - self.x
        dy = py - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            dir_x = dx / dist
            dir_y = dy / dist
            
            perp_x = -dir_y
            perp_y = dir_x

            self.angulo_espiral += 0.08
            fator_espiral = math.sin(self.angulo_espiral) * 1.3

            vx = dir_x + perp_x * fator_espiral
            vy = dir_y + perp_y * fator_espiral
            norma = math.hypot(vx, vy)

            if norma > 0:
                self.x += (vx / norma) * self.velocidade
                self.y += (vy / norma) * self.velocidade

    def desenhar(self, tela, camera):
        cx, cy = camera.aplicar(self.x, self.y)
        pygame.draw.circle(tela, COR_ROXO, (int(cx), int(cy)), self.raio)
        largura_barra = 28
        pct = max(0, self.vida / self.vida_max)
        pygame.draw.rect(tela, (40, 0, 40), (cx - 14, cy - 24, largura_barra, 4))
        pygame.draw.rect(tela, (200, 80, 255), (cx - 14, cy - 24, largura_barra * pct, 4))


class Item:
    def __init__(self, x, y, tipo):
        self.x = x
        self.y = y
        self.tipo = tipo  
        self.raio = 10

    def desenhar(self, tela, camera):
        cx, cy = camera.aplicar(self.x, self.y)
        cor = COR_ITEM_VIDA if self.tipo == 'vida' else COR_ITEM_MUNICAO
        pygame.draw.circle(tela, cor, (int(cx), int(cy)), self.raio)
        
        fonte_item = pygame.font.SysFont("Arial", 12, bold=True)
        simbolo = "+" if self.tipo == 'vida' else "M"
        txt = fonte_item.render(simbolo, True, (0, 0, 0))
        tela.blit(txt, txt.get_rect(center=(int(cx), int(cy))))


def obter_areas_ativas(px, py):
    if px < LARGURA_MUNDO / 2:
        cols = (0, 1)
    else:
        cols = (1, 2)

    if py < ALTURA_MUNDO / 2:
        lins = (0, 1)
    else:
        lins = (1, 2)

    areas_ativas = set()
    for l in lins:
        for c in cols:
            areas_ativas.add((l, c))

    return areas_ativas


def gerar_horda(inimigos, itens, quantidade_inimigos=20, quantidade_itens=10):
    for _ in range(quantidade_inimigos):
        x = random.randint(50, LARGURA_MUNDO - 50)
        y = random.randint(50, ALTURA_MUNDO - 50)
        if random.random() < 0.6:
            inimigos.append(InimigoVermelho(x, y))
        else:
            inimigos.append(InimigoRoxo(x, y))

    for _ in range(quantidade_itens):
        x = random.randint(50, LARGURA_MUNDO - 50)
        y = random.randint(50, ALTURA_MUNDO - 50)
        tipo = 'vida' if random.random() < 0.5 else 'municao'
        itens.append(Item(x, y, tipo))


def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    pygame.display.set_caption("Representação do Mundo - Sobrevivência em Grid 3x3")
    relogio = pygame.time.Clock()
    fonte = pygame.font.SysFont("Consolas", 18, bold=True)
    fonte_pequena = pygame.font.SysFont("Consolas", 14, bold=True)
    fonte_grande = pygame.font.SysFont("Consolas", 36, bold=True)

    camera = Camera(LARGURA_TELA, ALTURA_TELA)
    player = Player(LARGURA_MUNDO // 2, ALTURA_MUNDO // 2)

    inimigos = []
    itens = []
    tiros = []
    
    gerar_horda(inimigos, itens, quantidade_inimigos=20, quantidade_itens=10)

    tempo_inicial = time.time()
    ultimo_respawn_horda = time.time()
    tempo_sobrevivencia = 0.0
    INTERVALO_HORDA = 20.0

    rodando = True
    game_over = False

    while rodando:
        tempo_atual = time.time()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif evento.type == pygame.KEYDOWN:
                if not game_over:
                    if evento.key == pygame.K_z:
                        player.usar_dash()
                    elif evento.key == pygame.K_x:
                        player.atirar(tiros)
                else:
                    if evento.key == pygame.K_r:
                        main()
                        return

        if not game_over:
            tempo_sobrevivencia = tempo_atual - tempo_inicial

            teclas = pygame.key.get_pressed()
            player.mover(teclas)
            camera.atualizar(player.x, player.y)

            areas_ativas = obter_areas_ativas(player.x, player.y)

            if tempo_atual - ultimo_respawn_horda >= INTERVALO_HORDA:
                gerar_horda(inimigos, itens, quantidade_inimigos=20, quantidade_itens=8)
                ultimo_respawn_horda = tempo_atual

            for tiro in tiros[:]:
                tiro.atualizar()
                if not tiro.ativo:
                    tiros.remove(tiro)
                    continue

                for inimigo in inimigos[:]:
                    if inimigo in tiro.atingidos:
                        continue  
                    
                    dist_tiro = math.hypot(tiro.x - inimigo.x, tiro.y - inimigo.y)
                    if dist_tiro < (tiro.raio + inimigo.raio):
                        inimigo.vida -= tiro.dano
                        tiro.atingidos.add(inimigo)  
                        if inimigo.vida <= 0:
                            inimigos.remove(inimigo)

            for inimigo in inimigos[:]:
                lin = int(inimigo.y // ALTURA_AREA)
                col = int(inimigo.x // LARGURA_AREA)

                if (lin, col) in areas_ativas:
                    inimigo.atualizar(player.x, player.y)

                    dist_player = math.hypot(player.x - inimigo.x, player.y - inimigo.y)
                    if dist_player < (player.raio + inimigo.raio) and player.cooldown_invuln == 0:
                        player.vida -= inimigo.dano_contato
                        player.cooldown_invuln = 30
                        if inimigo in inimigos:
                            inimigos.remove(inimigo)

            if player.vida <= 0:
                player.vida = 0
                game_over = True

            for item in itens[:]:
                dist_item = math.hypot(player.x - item.x, player.y - item.y)
                if dist_item < (player.raio + item.raio):
                    if item.tipo == 'vida':
                        player.vida = min(player.vida_max, player.vida + 10)
                        itens.remove(item)
                    elif item.tipo == 'municao':
                        if player.municao < player.municao_max:
                            player.municao += 1
                            itens.remove(item)

        tela.fill(COR_FUNDO)

        areas_ativas_atuais = obter_areas_ativas(player.x, player.y)
        for lin in range(GRID_LINHAS):
            for col in range(GRID_COLUNAS):
                area_x = col * LARGURA_AREA
                area_y = lin * ALTURA_AREA
                screen_x, screen_y = camera.aplicar(area_x, area_y)
                
                rect_area = pygame.Rect(screen_x, screen_y, LARGURA_AREA, ALTURA_AREA)
                cor_celula = COR_AREA_ATIVA if (lin, col) in areas_ativas_atuais else COR_AREA_INATIVA
                pygame.draw.rect(tela, cor_celula, rect_area)
                pygame.draw.rect(tela, COR_GRID, rect_area, 2)


        for item in itens:
            item.desenhar(tela, camera)

        for tiro in tiros:
            tiro.desenhar(tela, camera)

        for inimigo in inimigos:
            inimigo.desenhar(tela, camera)

        player.desenhar(tela, camera)

        pygame.draw.rect(tela, COR_HUD_BG, (10, 10, 280, 85), border_radius=8)
        
        minutos = int(tempo_sobrevivencia // 60)
        segundos = int(tempo_sobrevivencia % 60)
        txt_tempo = fonte.render(f"Tempo: {minutos:02d}:{segundos:02d}", True, COR_TEXTO)
        tela.blit(txt_tempo, (20, 20))

        txt_vida = fonte.render(f"Vida: {player.vida}/{player.vida_max}", True, COR_TEXTO)
        tela.blit(txt_vida, (20, 45))
        pygame.draw.rect(tela, (80, 20, 20), (140, 48, 130, 14), border_radius=4)
        pct_vida = max(0, player.vida / player.vida_max)
        pygame.draw.rect(tela, (50, 220, 100), (140, 48, 130 * pct_vida, 14), border_radius=4)

        tempo_prox_horda = int(INTERVALO_HORDA - ((tempo_atual - ultimo_respawn_horda) % INTERVALO_HORDA))
        txt_horda = fonte.render(f"Próxima Horda: {tempo_prox_horda}s", True, (200, 200, 100))
        tela.blit(txt_horda, (20, 70))

        pygame.draw.rect(tela, COR_HUD_BG, (LARGURA_TELA - 110, 10, 100, 100), border_radius=8)
        for l in range(3):
            for c in range(3):
                cor_m = (100, 255, 150) if (l, c) in areas_ativas_atuais else (60, 60, 70)
                pygame.draw.rect(tela, cor_m, (LARGURA_TELA - 100 + c * 28, 20 + l * 28, 24, 24), border_radius=3)

        pygame.draw.rect(tela, COR_HUD_BG, (LARGURA_TELA - 260, ALTURA_TELA - 100, 250, 90), border_radius=8)
        
        if player.cooldown_dash == 0:
            txt_dash = fonte_pequena.render("Dash (Z): PRONTO", True, (100, 255, 150))
        else:
            seg_cd = player.cooldown_dash / 60.0
            txt_dash = fonte_pequena.render(f"Dash (Z): {seg_cd:.1f}s", True, (255, 100, 100))
        tela.blit(txt_dash, (LARGURA_TELA - 250, ALTURA_TELA - 92))

        txt_mun = fonte_pequena.render("Tiro (X):", True, COR_TEXTO)
        tela.blit(txt_mun, (LARGURA_TELA - 250, ALTURA_TELA - 68))

        for i in range(player.municao_max):
            cor_bullet = COR_ITEM_MUNICAO if i < player.municao else (60, 60, 70)
            pygame.draw.circle(tela, cor_bullet, (LARGURA_TELA - 170 + i * 35, ALTURA_TELA - 35), 10)
            pygame.draw.circle(tela, (255, 255, 255), (LARGURA_TELA - 170 + i * 35, ALTURA_TELA - 35), 10, 1)

        if game_over:
            sombra = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
            sombra.fill((0, 0, 0, 200))
            tela.blit(sombra, (0, 0))

            txt_go = fonte_grande.render("VOCÊ MORREU!", True, COR_VERMELHO)
            txt_res = fonte.render(f"Tempo de Sobrevivência: {minutos:02d}:{segundos:02d}", True, COR_TEXTO)
            txt_restart = fonte.render("Pressione 'R' para Reiniciar", True, COR_ITEM_MUNICAO)

            tela.blit(txt_go, txt_go.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2 - 50)))
            tela.blit(txt_res, txt_res.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2 + 10)))
            tela.blit(txt_restart, txt_restart.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2 + 60)))

        pygame.display.flip()
        relogio.tick(FPS)

if __name__ == "__main__":
    main()