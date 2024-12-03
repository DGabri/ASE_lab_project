import axios from 'axios'

const getUserCollection = async (user_id, access_token) => {
    const axiosInstance = axios.create({
        httpsAgent: false,
        validateStatus: () => true
    })

    const response = await axiosInstance.get(
        `https://localhost:3000/user/player/collection/${user_id}`,
        {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${access_token}`
            }
        }
    )

    if (response.status != 200) {
        throw new Error(response.data.err)  
    }

    const collection = {}
    
    for (const piece of response.data.collection) {
        if (piece.gacha_id in collection) {
            collection[piece.gacha_id] += 1
        }
        else {
            collection[piece.gacha_id] = 1
        }
    }

    return collection
}

export default getUserCollection