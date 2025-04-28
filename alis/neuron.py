import heapq

# ===== ALIS Neuron 클래스 =====
class Neuron:
    def __init__(self, name, threshold=1.0, base_decay=0.1, refractory_duration=1.0):
        self.name = name
        self.queue = []  # (event_time, weight)
        self.potential = 0.0
        self.threshold = threshold
        self.base_decay = base_decay
        self.refractory_duration = refractory_duration
        self.refractory = False
        self.refractory_end_time = 0.0
        self.last_update_time = 0.0
        self.targets = []  # (target_neuron, weight, delay)
        self.history = []

    def add_target(self, target_neuron, weight=1.0, delay=0.0):
        self.targets.append((target_neuron, weight, delay))

    def receive_signal(self, event_time, weight):
        heapq.heappush(self.queue, (event_time, weight))
        self.log_event(event_time, "Signal Received", f"Weight: {weight:.2f}")

    def force_fire(self, current_time):
        if not self.refractory:
            self.potential = self.threshold
            self.fire(current_time)
        else:
            self.log_event(current_time, "Force Fire Attempt Blocked", "Still in Refractory")

    def decay(self, current_time):
        elapsed = current_time - self.last_update_time
        self.potential -= self.base_decay * elapsed
        if self.potential <= 0:
            self.potential = 0
        self.last_update_time = current_time
        self.log_event(current_time, "Decay Applied", f"Elapsed: {elapsed:.2f}")

    def process_until(self, current_time):
        while self.queue and self.queue[0][0] <= current_time:
            event_time, weight = heapq.heappop(self.queue)

            if self.refractory and event_time < self.refractory_end_time:
                self.log_event(event_time, "Signal Ignored (Refractory)", f"Weight: {weight:.2f}")
                continue

            if self.refractory and event_time >= self.refractory_end_time:
                self.refractory = False
                self.log_event(event_time, "Refractory Ended")

            self.decay(event_time)
            self.potential += weight
            self.log_event(event_time, "Potential Increased", f"Added: {weight:.2f}, New Potential: {self.potential:.2f}")

            if self.potential >= self.threshold:
                self.fire(event_time)

    def fire(self, event_time):
        self.potential = 0.0
        self.refractory = True
        self.refractory_end_time = event_time + self.refractory_duration
        self.log_event(event_time, "Neuron Fired", f"Entering Refractory until {self.refractory_end_time:.2f}")

        # 발화 기록도 네트워크 흐름에 추가
        network_signal_log.append({
            "type": "fire",
            "neuron": self.name,
            "time": event_time
        })

        for target, weight, delay in self.targets:
            arrival_time = event_time + delay
            target.receive_signal(arrival_time, weight)
            # 신호 송신 기록
            network_signal_log.append({
                "type": "signal",
                "from": self.name,
                "to": target.name,
                "weight": weight,
                "arrival_time": arrival_time
            })

    def log_event(self, current_time, event_type, details=""):
        self.history.append((current_time, event_type, details))

    def print_queue(self, start_time=None, end_time=None):
        for event_time, weight in sorted(self.queue):
            if (start_time is not None and event_time < start_time):
                continue
            if (end_time is not None and event_time > end_time):
                continue
            print(f"  Time: {event_time:.2f}, Weight: {weight:.2f}")

    def print_history(
        self,
        start_time=None,
        end_time=None,
        show_signals=True,
        show_fires=True,
        show_decay=True,
        show_refractory=True,
        show_force_block=True
    ):
        for time_stamp, event, detail in self.history:
            if (start_time is not None and time_stamp < start_time):
                continue
            if (end_time is not None and time_stamp > end_time):
                continue
            if ("Signal Received" in event and not show_signals):
                continue
            if ("Neuron Fired" in event and not show_fires):
                continue
            if ("Decay Applied" in event and not show_decay):
                continue
            if ("Refractory Ended" in event and not show_refractory):
                continue
            if ("Force Fire Attempt Blocked" in event and not show_force_block):
                continue
            print(f"[{time_stamp:.2f}] {event} | {detail}")

# ===== 전역 네트워크 신호 흐름 기록 리스트 =====
network_signal_log = []

# ===== 네트워크 출력 제어 함수들 =====

def print_network_queues(neurons, mode="network", target_names=None, start_time=None, end_time=None):
    if mode == "single":
        for neuron in neurons:
            if (target_names is None) or (neuron.name in target_names):
                print(f"\n=== {neuron.name} Current Queue ===")
                neuron.print_queue(start_time=start_time, end_time=end_time)
    elif mode == "network":
        combined = []
        for neuron in neurons:
            if (target_names is None) or (neuron.name in target_names):
                combined.extend([(event_time, neuron.name, weight) for event_time, weight in neuron.queue])
        combined = sorted(combined)
        print("\n=== Combined Network Queue ===")
        for event_time, name, weight in combined:
            if (start_time is not None and event_time < start_time):
                continue
            if (end_time is not None and event_time > end_time):
                continue
            print(f"[{name}] Time: {event_time:.2f}, Weight: {weight:.2f}")

def print_network_history(neurons, target_names=None, start_time=None, end_time=None, show_signals=True, show_fires=True, show_decay=True, show_refractory=True, show_force_block=True):
    for neuron in neurons:
        if (target_names is None) or (neuron.name in target_names):
            print(f"\n=== {neuron.name} Event History ===")
            neuron.print_history(
                start_time=start_time,
                end_time=end_time,
                show_signals=show_signals,
                show_fires=show_fires,
                show_decay=show_decay,
                show_refractory=show_refractory,
                show_force_block=show_force_block
            )

def print_network_signal_log(start_time=None, end_time=None):
    sorted_log = sorted(network_signal_log, key=lambda x: x["time"] if x["type"]=="fire" else x["arrival_time"])
    print("\n=== Network Signal and Firing Flow ===")
    for entry in sorted_log:
        if entry["type"] == "fire":
            if (start_time is not None and entry["time"] < start_time):
                continue
            if (end_time is not None and entry["time"] > end_time):
                continue
            print(f"[{entry['time']:.2f}] {entry['neuron']} FIRED")
        elif entry["type"] == "signal":
            if (start_time is not None and entry["arrival_time"] < start_time):
                continue
            if (end_time is not None and entry["arrival_time"] > end_time):
                continue
            print(f"[{entry['arrival_time']:.2f}] {entry['from']} → {entry['to']} | Weight: {entry['weight']:.2f}")
    print("============================\n")

# ===== 예제: 기본 네트워크 세팅 및 시뮬레이션 =====

A = Neuron(name="A", threshold=1.0, base_decay=0.05, refractory_duration=1.0)
B = Neuron(name="B", threshold=1.0, base_decay=0.05, refractory_duration=1.0)

neurons = [A, B]

A.add_target(B, weight=1.0, delay=1.0)
B.add_target(A, weight=1.0, delay=1.0)

A.force_fire(current_time=0.0)

# ===== 이벤트 점프형 시뮬레이션 =====

current_time = 0.0
end_time = 5.0

while True:
    next_times = [neuron.queue[0][0] for neuron in neurons if neuron.queue]
    if not next_times:
        break

    next_event_time = min(next_times)

    if next_event_time > end_time:
        break

    for neuron in neurons:
        neuron.process_until(next_event_time)

    current_time = next_event_time

# ===== 출력 예시 =====

print_network_queues(neurons, mode="network", start_time=0.0, end_time=5.0)
print_network_history(neurons, start_time=0.0, end_time=5.0, show_signals=False, show_fires=True)
print_network_signal_log(start_time=0.0, end_time=5.0)
