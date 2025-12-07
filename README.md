# starcraft- 미니게임
테란 VS 저그(컴퓨터)
당신은 테란입니다. 
새로운 행성을 찾아 자원을 수집하는 임무를 받아 우주를 떠다닙니다.
이때 새로운 행성을 발견합니다. 
이곳에는 풍부한 미네랄과 베스핀 가스가 매장되어 있습니다.
수월하게 자원을 수집하기 위해 자원이 풍부한 포인트에 커맨드 센터를 행성에 착륙시킨 후,
SCV를 통해 자원을 수집하며 정찰을 합니다. 
그런데....
<h3>두근...</h3> <h2>두근...</h2> <h1>두근...</h1>
이런! 다른 포인트에 저그가 해처리를 피고 자원을 채취하고 있습니다.
커멘드 센터에서 오버로드를 식별하였습니다.
저그도 우리를 알아차리고 전투준비에 돌입합니다.
정찰 결과 저그만 물리친다면 이 행성을 차지할 수 있습니다.
전투에 승리하여 행성을 차지하세요!


총 3라운드 진행
1라운드 : 마린으로 저글링을 방어하세요 / 저글링 36마리
2라운드 : 마린과 터렛으로 뮤탈을 방어하세요 / 저글링(속도 증가) 12마리, 뮤탈 12마리
3라운드 : 마린과 탱크로 저글링, 울트라를 방어하세요 / 저글링(속도 증가, 공격속도 증가) 12마리, 울트라 4마리
*다음 라운드로 넘어갈 때 일꾼과 자원 상황, 병력은 유지
*2라운드에 멀티 생성 가능(파괴되면 저그 진영에서 3라운드에 감염된 테란 생성), 생성 가능한 장소는 중앙 1곳
유닛 이동은 좌클릭 : 공격(이동하지 않을때는 자동 공격)
*일꾼은 자동으로 움직입니다. 만지면 안되요,...

코드 분석
이 게임은 Pygame으로 제작된 게임으로 미네랄을 채취하여 병력을 뽑고 전투를 한다.
클래스로는 

Unit :
모든 유닛·건물의 기본 동작 (이동, 공격, AI, HP 표시 등)

Base :
플레이어/적 기지, 파괴 시 승패 결정

Mineral :
자원 노드 (일꾼이 자동 채취)

Game :
UI, 입력 처리, 라운드 시스템, 스폰 로직, 렌더링 포함한 전체 게임 관리


이 코드의 핵심 특징은
가장 가까우면서 작업자가 적은 미네랄을 자동 선택하기 위해
target = min(minerals, key=lambda m: (m.workers, distance(worker.pos, m.pos)))
으로 작업자 수가 적은 미네랄 중 그 중에서 거리가 더 가까운 미네랄을 고르는 것이고

유닛끼리 겹치지 않도록 분리 AI 적용으로
d = distance(self.pos, other.pos)
if d < separation_range:          
            dx = self.pos[0] - other.pos[0]
            dy = self.pos[1] - other.pos[1]
            self.pos[0] += dx * 0.02       
            self.pos[1] += dy * 0.02
으로 반발력을 적용하여 곂쳐서 발생하는 버그를 수정하였다.

벙커 탑승 시스템 구현으로
if isinstance(target, Bunker) and isinstance(unit, Marine):
    if target.can_enter(unit):
        target.garrison.append(unit)      
        unit.is_hidden = True 
벙커 내부 유닛 수와 유닛을 화면에서 숨김으로 탐승을 표현하고
total_damage = base_damage + sum(m.dmg for m in bunker.garrison)
enemy.hp -= total_damage
마린이 들어간 수로 데이지를 계산하였다.

마지막으로 자동 전투로
d = distance(self.pos, self.target.pos)
if d <= self.attack_range:
    self.attack(self.target)
으로 사거리 안이면 공격하고 
else:
    self.move_towards(self.target.pos)
사거리 밖이면 이동한다.


