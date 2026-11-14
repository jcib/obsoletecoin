# Native build compatibility

Boost >=1.91 no longer permits deriving index-list wrapper structs from multi_index::indexed_by. Four inherited wrappers were converted into type aliases, retaining every index/key/comparator. Reference: Bitcoin Core https://github.com/bitcoin/bitcoin/pull/35175 . This is a build compatibility adjustment, not a change to monetary or proof-of-work rules. Both Linux and Windows full suites are required after the adjustment.
