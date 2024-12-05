import axios from 'axios'

const addAuction = async (access_token, auction) => {
    const axiosInstance = axios.create({
        httpsAgent: false,
        validateStatus: () => true
    })

    const response = await axiosInstance.post(
        'https://localhost:3000/auction/create_auction', auction,
        {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${access_token}`
            }
        }
    )
    
    if (response.status != 201) {
        throw new Error(response.data.err)  
    }
}

export default addAuction