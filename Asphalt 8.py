
import pygame
import time
import random
import os
import heapq
import platform
import asyncio  # Added import for asyncio
from collections import deque

pygame.init()
pygame.mixer.init()

gameWindow = pygame.display.set_mode((1200,700))
pygame.display.set_caption("Asphalt 8 Airborne")

clock = pygame.time.Clock()
fps = 60

font1 = pygame.font.SysFont("Franklin Gothic Demi Cond",50)

car = pygame.image.load("data/images/Car.png")
car = pygame.transform.scale(car,(150,150)).convert_alpha()

road = pygame.image.load("data/images/Road.png")
road = pygame.transform.scale(road,(400,700)).convert_alpha()

sand = pygame.image.load("data/images/Sand.jpg")
sand = pygame.transform.scale(sand,(150,700)).convert_alpha()

leftDisp = pygame.image.load("data/images/LeftDisplay.png")
leftDisp = pygame.transform.scale(leftDisp,(250,700)).convert_alpha()

rightDisp = pygame.image.load("data/images/RightDisplay.png")
rightDisp = pygame.transform.scale(rightDisp,(250,700)).convert_alpha()

tree = pygame.image.load("data/images/Tree.png")
tree = pygame.transform.scale(tree,(185,168)).convert_alpha()
treeLXY = [[290,0],[290,152.5],[290,305],[290,457.5],[290,610]]
treeRXY = [[760,0],[760,152.5],[760,305],[760,457.5],[760,610]]

strip = pygame.image.load("data/images/Strip.png")
strip = pygame.transform.scale(strip,(25,90)).convert_alpha()
stripXY = [[593,0],[593,152.5],[593,305],[593,457.5],[593,610]]

explosion = pygame.image.load("data/images/Explosion.png")
explosion = pygame.transform.scale(explosion,(290,164)).convert_alpha()

fuel = pygame.image.load("data/jpeg/Fuel.jpeg")
fuel = pygame.transform.scale(fuel,(98,104)).convert_alpha()

comingCars,goingCars = [],[]
speedCC = [13,14,15,14,14,15,13,14,15]
speedGC = [8,6,7,5,8,7,8,6,8]

for i in range(1,10):
    CCi = pygame.image.load("data/images/Coming Cars/"+"CC"+str(i)+".png")
    CCi = pygame.transform.scale(CCi, (75, 158)).convert_alpha()
    comingCars.append([CCi,speedCC[i-1]])
    GCi = pygame.image.load("data/images/Going Cars/"+"GC"+str(i)+".png").convert_alpha()
    GCi = pygame.transform.scale(GCi,(75,158)).convert_alpha()
    goingCars.append([GCi,speedGC[i-1]])

# Valid lane x-coordinates for binary search
valid_lanes = [330, 360, 390, 420, 450, 480, 510, 540, 570, 600, 630, 660, 690, 720]

# Graph for BFS and Dijkstra’s
lane_graph = {
    430: [460], 460: [430, 490], 490: [460, 530], 530: [490],  # Coming cars lanes
    620: [650], 650: [620, 680], 680: [650, 710], 710: [680]   # Going cars lanes
}

# Flag to toggle complexity display
show_complexities = False

def distance(carX,obstX,carY,obstY,isFuel=False):
    if not isFuel:
        carX += 75
        carY += 75
        obstX += 37
        obstY += 79
        return abs(carX - obstX) < 55 and abs(carY - obstY) < 130
    else:
        carX += 75
        carY += 75
        obstX += 98
        obstY += 104
        return abs(carX - obstX) < 70 and abs(carY - obstY) < 80

def binary_search_lane(carX):
    left, right = 0, len(valid_lanes) - 1
    while left <= right:
        mid = (left + right) // 2
        if valid_lanes[mid] == carX:
            return True
        elif valid_lanes[mid] < carX:
            left = mid + 1
        else:
            right = mid - 1
    return carX >= valid_lanes[0] and carX <= valid_lanes[-1]

def bfs_lane_change(start_x, target_x):
    if start_x == target_x:
        return start_x
    queue = deque([start_x])
    visited = {start_x}
    parent = {start_x: None}
    while queue:
        current = queue.popleft()
        for neighbor in lane_graph.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)
                if neighbor == target_x:
                    while parent[neighbor] != start_x:
                        neighbor = parent[neighbor]
                    return neighbor
    return start_x  # No path; stay in place

def dijkstra_safe_fuel(obstacle_x):
    fuel_positions = list(range(420, 711, 30))
    distances = {x: float('inf') for x in fuel_positions}
    distances[420] = 0
    pq = [(0, 420)]
    while pq:
        dist, current = heapq.heappop(pq)
        if dist > distances[current]:
            continue
        for next_x in fuel_positions:
            if abs(next_x - current) <= 30:
                weight = min(abs(next_x - x) for x in obstacle_x)
                new_dist = distances[current] + (1000 / weight)
                if new_dist < distances[next_x]:
                    distances[next_x] = new_dist
                    heapq.heappush(pq, (new_dist, next_x))
    return min(fuel_positions, key=lambda x: distances[x])

def textOnScreen(text,color,x,y,font):
    screenText = font.render(text,True,color)
    gameWindow.blit(screenText,[x,y])

def display_complexities():
    complexities = [
        ("Collision Detection (distance)", "O(1)", "O(1)"),
        ("Binary Search (binary_search_lane)", "O(log n)", "O(1)"),
        ("BFS (bfs_lane_change)", "O(1)", "O(1)"),
        ("Dijkstra’s (dijkstra_safe_fuel)", "O(1)", "O(1)"),
        ("Game Loop", "O(1) per frame", "O(1)")
    ]
    y_offset = 100
    gameWindow.fill((0, 0, 0, 200))  # Semi-transparent overlay
    textOnScreen("Algorithm Complexities", (255, 255, 0), 400, 50, font1)
    for algo, time_c, space_c in complexities:
        textOnScreen(f"{algo}:", (255, 255, 255), 300, y_offset, font1)
        textOnScreen(f"Time: {time_c}, Space: {space_c}", (255, 0, 0), 300, y_offset + 40, font1)
        y_offset += 100

def slowDown(carX,carY,dist,highscore):
    stripXY_ = [[593, 0], [593, 152.5], [593, 305], [593, 457.5], [593, 610]]
    exitScreen = False
    stripSpeed = 2
    start = time.time()
    while not exitScreen:
        if time.time() - start > 3:
            stripSpeed = 1
        if time.time() - start > 6:
            exitScreen = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exitScreen = True
        gameWindow.fill((0,0,0))
        gameWindow.blit(leftDisp, (0, 0))
        textOnScreen("DISTANCE", (255, 255, 0), 27, 388, font1)
        textOnScreen(str(dist) + " Kms", (255, 0, 0), 56, 480, font1)
        textOnScreen("FUEL", (255, 255, 0), 73, 90, font1)
        textOnScreen(str(0.00) + ' %', (255, 0, 0), 75, 184, font1)
        gameWindow.blit(rightDisp, (950, 0))
        textOnScreen("HIGHSCORE", (255, 255, 0), 958, 236, font1)
        disp = f"{highscore:02d}" if highscore < 10 else str(highscore)
        textOnScreen(disp + " Kms", (255, 0, 0), 1005, 342, font1)
        gameWindow.blit(road, (400, 0))
        gameWindow.blit(sand,(250,0))
        gameWindow.blit(sand,(800,0))
        for i in range(len(stripXY_)):
            stripXY_[i][1] += stripSpeed
            if stripXY_[i][1] > 700:
                stripXY_[i] = [593, -60]
        for i in range(len(treeLXY)):
            treeLXY[i][1] += stripSpeed
            if treeLXY[i][1] > 700:
                treeLXY[i] = [290,-60]
        for i in range(len(treeRXY)):
            treeRXY[i][1] += stripSpeed
            if treeRXY[i][1] > 700:
                treeRXY[i] = [760,-60]
        for X,Y in stripXY_:
            gameWindow.blit(strip,(X,Y))
        for treeX,treeY in treeLXY:
            gameWindow.blit(tree,(treeX,treeY))
        for treeX,treeY in treeRXY:
            gameWindow.blit(tree,(treeX,treeY))
        gameWindow.blit(car,(carX,carY))
        if show_complexities:
            display_complexities()
        pygame.display.update()

def gameLoop():
    global show_complexities
    pygame.mixer.music.load("data/audios/lmn.mp3")
    pygame.mixer.music.play()
    time.sleep(1)

    carX, carY = 625, 540
    drift = 4
    carSpeedX = 0
    obstacleXY = [[460,-10],[710,-300]]
    c1, c2 = random.randint(0,8), random.randint(0,8)
    if c1 == c2:
        c1 = random.randint(0,8)
    obstacleSpeed = [comingCars[c1][1], goingCars[c2][1]]
    obstacles = [comingCars[c1][0], goingCars[c2][0]]
    stripSpeed = 9
    exitGame = False
    gameOver = False
    explode = False
    fuelCount = 50
    fuelX, fuelY = random.randint(420,620), -1000
    fuelSpeed = 8
    dist = 0

    if not os.path.exists("data/Highscore.txt"):
        with open("data/Highscore.txt", "w") as f:
            f.write("0")
        highscore = 0
    else:
        with open("data/Highscore.txt", "r") as f:
            highscore = int(f.read())

    slow = False
    plotFuel = True
    start1 = time.time()
    start = [start1, start1]
    start2 = start1
    start3 = start1
    start4 = start1
    start_bfs = start1
    arrival = [2, 3.5]

    while not exitGame:
        if gameOver:
            if slow:
                slowDown(carX, carY, dist, highscore)
            time.sleep(2)
            pygame.mixer.music.stop()
            pygame.mixer.music.load("data/audios/rtn.mp3")
            pygame.mixer.music.play()
            exitScreen = False
            go = pygame.image.load("data/jpeg/Game Over.jpg")
            go = pygame.transform.scale(go,(1239,752)).convert_alpha()
            with open("data/Highscore.txt","w") as f:
                f.write(str(highscore))
            while not exitScreen:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        exitScreen = True
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            pygame.mixer.music.stop()
                            homeScreen()
                        elif event.key == pygame.K_c:
                            show_complexities = not show_complexities
                gameWindow.fill((0,0,0))
                gameWindow.blit(go,(0,0))
                disp = f"{dist:02d}" if dist < 10 else str(dist)
                textOnScreen(disp,(255,0,0),540,429,font1)
                if show_complexities:
                    display_complexities()
                pygame.display.update()
                clock.tick(fps)
            pygame.quit()
            return
        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exitGame = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        carSpeedX = drift
                    elif event.key == pygame.K_LEFT:
                        carSpeedX = -drift
                    elif event.key == pygame.K_a:
                        obstacleXY[0][0] -= 20
                    elif event.key == pygame.K_d:
                        obstacleXY[1][0] += 20
                    elif event.key == pygame.K_c:
                        show_complexities = not show_complexities
            carX += carSpeedX
            fuelY += fuelSpeed
            if time.time() - start4 >= 2:
                dist += 1
                if dist > highscore:
                    highscore = dist
                start4 = time.time()
            if time.time() - start2 >= 3:
                fuelCount -= 5
                start2 = time.time()
            if distance(carX, fuelX, carY, fuelY, True) and plotFuel:
                plotFuel = False
                fuelCount += 20
            for i in range(len(obstacleXY)):
                obstacleXY[i][1] += obstacleSpeed[i]
            fuelper = fuelCount / 50
            if fuelper >= 1:
                fuelper = 1
            gameWindow.fill((0,0,0))
            gameWindow.blit(leftDisp,(0,0))
            textOnScreen("DISTANCE", (255, 255, 0),27,388,font1)
            disp = f"{dist:02d}" if dist < 10 else str(dist)
            textOnScreen(disp + " Kms",(255,0,0),56,480,font1)
            textOnScreen("FUEL",(255,255,0),73,90,font1)
            textOnScreen(str(fuelper*100) + ' %',(255,0,0),60,184,font1)
            gameWindow.blit(rightDisp, (950, 0))
            textOnScreen("HIGHSCORE",(255,255,0),958,236,font1)
            disp = f"{highscore:02d}" if highscore < 10 else str(highscore)
            textOnScreen(disp + " Kms",(255,0,0),1005,342,font1)
            gameWindow.blit(road,(400,0))
            gameWindow.blit(sand, (250, 0))
            gameWindow.blit(sand, (800, 0))
            if fuelCount == 0:
                gameOver = True
                slow = True
            if not binary_search_lane(carX):
                pygame.mixer.music.load("data/audios/Crash.mp3")
                pygame.mixer.music.play()
                gameOver = True
                explode = True
            for i in range(len(obstacleXY)):


                if distance(carX, obstacleXY[i][0], carY, obstacleXY[i][1]):
                    pygame.mixer.music.load("data/audios/Crash.mp3")
                    pygame.mixer.music.play()
                    gameOver = True
                    explode = True
                    break
            for i in range(len(stripXY)):
                stripXY[i][1] += stripSpeed
                if stripXY[i][1] > 700:
                    stripXY[i] = [593,-60]
            for i in range(len(treeLXY)):
                treeLXY[i][1] += stripSpeed
                if treeLXY[i][1] > 700:
                    treeLXY[i] = [290, -60]
            for i in range(len(treeRXY)):
                treeRXY[i][1] += stripSpeed
                if treeRXY[i][1] > 700:
                    treeRXY[i] = [760,-60]
            for stripX,stripY in stripXY:
                gameWindow.blit(strip,(stripX,stripY))
            if fuelY < 750:
                if plotFuel:
                    gameWindow.blit(fuel,(fuelX,fuelY))
            gameWindow.blit(car,(carX,carY))
            for i in range(len(obstacleXY)):
                if obstacleXY[i][1] < 750:
                    gameWindow.blit(obstacles[i],(obstacleXY[i][0], obstacleXY[i][1]))
            for treeX, treeY in treeLXY:
                gameWindow.blit(tree, (treeX, treeY))
            for treeX, treeY in treeRXY:
                gameWindow.blit(tree, (treeX, treeY))
            if time.time() - start[0] >= arrival[0]:
                target_x = min(lane_graph.keys(), key=lambda x: abs(x - carX) if x <= 530 else float('inf'))
                x = bfs_lane_change(obstacleXY[0][0], target_x)
                obstacleXY[0] = [x, -10]
                c1 = random.randint(0,8)
                obstacles[0] = comingCars[c1][0]
                obstacleSpeed[0] = comingCars[c1][1]
                start[0] = time.time()
            if time.time() - start[1] >= arrival[1]:
                target_x = min(lane_graph.keys(), key=lambda x: abs(x - carX) if x >= 620 else float('inf'))
                x = bfs_lane_change(obstacleXY[1][0], target_x)
                obstacleXY[1] = [x, -10]
                c2 = random.randint(0,8)
                obstacles[1] = goingCars[c2][0]
                obstacleSpeed[1] = goingCars[c2][1]
                start[1] = time.time()
            if time.time() - start_bfs >= 5:
                for i, (x, y) in enumerate(obstacleXY):
                    target_x = min(lane_graph.keys(), key=lambda x: abs(x - carX) if (x <= 530 if i == 0 else x >= 620) else float('inf'))
                    obstacleXY[i][0] = bfs_lane_change(x, target_x)
                start_bfs = time.time()
            if time.time() - start3 >= 15:
                fuelX = dijkstra_safe_fuel([x for x, y in obstacleXY])
                fuelY = -500
                plotFuel = True
                start3 = time.time()
            if explode:
                gameWindow.blit(explosion,(carX - 63,carY))
            if show_complexities:
                display_complexities()
            pygame.display.update()
            clock.tick(fps)

def homeScreen():
    global show_complexities
    pygame.mixer.music.load("data/audios/rtn.mp3")
    pygame.mixer.music.play()
    if not os.path.exists("data/Highscore.txt"):
        with open("data/Highscore.txt","w") as f:
            f.write("0")
        highscore = 0
    else:
        with open("data/Highscore.txt","r") as f:
            highscore = int(f.read())
    background = pygame.image.load("data/jpeg/Background.jpg")
    background = pygame.transform.scale(background,(1213,760)).convert_alpha()
    exitScreen = False
    while not exitScreen:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exitScreen = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    pygame.mixer.music.stop()
                    gameLoop()
                elif event.key == pygame.K_c:
                    show_complexities = not show_complexities
        gameWindow.blit(background,(-6,-32))
        disp = f"{highscore:02d}" if highscore < 10 else str(highscore)
        textOnScreen(disp,(255,0,0),980,9,font1)
        if show_complexities:
            display_complexities()
        pygame.display.update()
        clock.tick(fps)
    pygame.quit()

async def main():
    homeScreen()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
